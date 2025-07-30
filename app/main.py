# インストールした discord.py を読み込む
import discord
from discord.ext import commands
from discord import ButtonStyle
from discord.ui import Button, View
from discord import app_commands
from datetime import datetime
from PayPaython_mobile import PayPay
import json
import os

# 自分のBotのアクセストークンに置き換えてください

TOKEN = os.environ.get("TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")

# 接続に必要なオブジェクトを生成
intents = discord.Intents.default()
intents.message_content = True  # コマンドを使用するために必要
intents.members = True  # メンバー参加イベントを使用するために必要
intents.guilds = True  # サーバー関連の機能を使用するために必要
client = discord.Client(intents=intents)

# スラッシュコマンド用のツリーを作成
tree = discord.app_commands.CommandTree(client)

# チケット作成ボタンのビュー
class TicketCreateView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="開く", style=ButtonStyle.green, emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        # チケットチャンネルを作成
        guild = interaction.guild
        user = interaction.user
        
        # チケットチャンネル名を生成
        channel_name = f"ticket-{user.name}"
        
        # チケットチャンネルを作成
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"チケット作成者: {user.name} ({user.id})"
            )
            
            # チケット内部の埋め込みメッセージを作成
            embed = discord.Embed(
                title="🎫 ticket",
                description="お問い合わせ内容をお聞かせください。",
                color=0x00ff00,
                timestamp=discord.utils.utcnow()
            )
            
            # 閉じるボタンのビューを作成
            close_view = TicketCloseView()
            
            await ticket_channel.send(
                content=f"<@&1398223291759460372>",  # 管理者ロールのメンション（ロールIDに変更してください）
                embed=embed,
                view=close_view
            )# 管理者ロールのメンション
            
            await interaction.response.send_message(
                f"✅ チケットチャンネル {ticket_channel.mention} を作成しました！",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ チケットの作成に失敗しました: {e}",
                ephemeral=True
            )

# チケット閉じるボタンのビュー
class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="閉じる", style=ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        # 確認用の埋め込みメッセージを作成
        embed = discord.Embed(
            title="🎫 ticket 閉じる確認",
            description="チケットを閉じる際の操作を選択してください。",
            color=0xff6b6b,
            timestamp=discord.utils.utcnow()
        )
        
        # 確認ボタンのビューを作成
        confirm_view = TicketConfirmView()
        
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

# チケット確認ボタンのビュー
class TicketConfirmView(View):
    def __init__(self):
        super().__init__(timeout=60)  # 60秒でタイムアウト
    
    @discord.ui.button(label="閉じる", style=ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        channel = interaction.channel
        try:
            await channel.delete()
            await interaction.response.send_message("✅ チケットを閉じました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ チケットの削除に失敗しました: {e}", ephemeral=True)
    
    @discord.ui.button(label="ログ保存", style=ButtonStyle.blurple, emoji="💾")
    async def save_log(self, interaction: discord.Interaction, button: Button):
        channel = interaction.channel
        
        # チャンネルのメッセージ履歴を取得
        messages = []
        async for message in channel.history(limit=100):
            if not message.author.bot:
                messages.append(f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author.name}: {message.content}")
        
        # ログをDMに送信
        try:
            # ボットのオーナーIDを設定（実際のDiscordユーザーIDに変更してください）
            owner_id = 1272824073310699585  # ここを実際のDiscordユーザーID（数字）に変更
            
            owner = await client.fetch_user(owner_id)
            log_content = f"**チケットログ: {channel.name}**\n\n" + "\n".join(reversed(messages))
            
            # 長いメッセージを分割
            if len(log_content) > 2000:
                chunks = [log_content[i:i+2000] for i in range(0, len(log_content), 2000)]
                for chunk in chunks:
                    await owner.send(chunk)
            else:
                await owner.send(log_content)
            
            await interaction.response.send_message("✅ ログをDMに送信しました。", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ ログの送信に失敗しました: {e}", ephemeral=True)
    
    @discord.ui.button(label="閉じない", style=ButtonStyle.gray, emoji="❌")
    async def cancel_close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("チケットを開いたままにします。", ephemeral=True)



# 認証パネルボタンのビュー
class VerificationPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="認証する", style=ButtonStyle.green, emoji="✅", custom_id="verify_1398205886345777232")
    async def verify_user(self, interaction: discord.Interaction, button: Button):
        role_id = 1398205886345777232
        role = interaction.guild.get_role(role_id)
        
        if role in interaction.user.roles:
            await interaction.response.send_message("✅ 既に認証済みです。", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message("✅ 認証が完了しました！", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ 認証に失敗しました: {e}", ephemeral=True)

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')
    print(f'ボット名: {client.user.name}')
    print(f'ボットID: {client.user.id}')
    print(f'インテント設定:')
    print(f'  - message_content: {client.intents.message_content}')
    print(f'  - members: {client.intents.members}')
    print(f'  - guilds: {client.intents.guilds}')
    print(f'接続中のサーバー数: {len(client.guilds)}')
    
    # スラッシュコマンドを同期
    try:
        print("スラッシュコマンドを同期中...")
        await tree.sync()
        print("スラッシュコマンドの同期が完了しました")
    except Exception as e:
        print(f"スラッシュコマンドの同期でエラー: {e}")
    
    # パネル再配置処理
    await setup_panels()

# パネル再配置関数
async def setup_panels():
    try:
        
        # 認証チャンネル
        verify_channel_id = 1398217513493594112
        verify_channel = client.get_channel(verify_channel_id)
        if verify_channel:
            print(f"認証チャンネルをクリア中: {verify_channel.name}")
            await clear_channel(verify_channel)
            
            # 認証パネルを作成
            embed = discord.Embed(
                title="🔐 認証パネル",
                description="下のボタンを押して認証を完了してください。",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            # 指定された画像を設定
            embed.set_image(url="https://cdn.discordapp.com/attachments/1398334731564748981/1398335054769557625/4577af4641060ee401cc2897e9fc9118.jpg?ex=6884fc80&is=6883ab00&hm=7d6982419819f961391baef08ce499024f9564a9f6bd9648612946c6e937eab0&")
            
            embed.set_footer(text="†NEO睡眠† 認証システム", icon_url=verify_channel.guild.icon.url if verify_channel.guild.icon else None)
            
            verify_view = VerificationPanelView()
            await verify_channel.send(embed=embed, view=verify_view)
            print("認証パネルを作成しました")
        
        # チケットチャンネル
        ticket_channel_id = 1398106755069776042
        ticket_channel = client.get_channel(ticket_channel_id)
        if ticket_channel:
            print(f"チケットチャンネルをクリア中: {ticket_channel.name}")
            await clear_channel(ticket_channel)
            
            # チケットシステムを作成
            embed = discord.Embed(
                title="🎫 ticket",
                description="お問い合わせ/自販機以外の商品購入はこちらから",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            ticket_view = TicketCreateView()
            await ticket_channel.send(embed=embed, view=ticket_view)
            print("チケットシステムを作成しました")

        
        print("すべてのパネルを再配置しました")
        
        # 自販機自動配置処理
        await setup_auto_vending_machines()
        
    except Exception as e:
        print(f"パネル再配置でエラーが発生しました: {e}")

# 自販機自動配置関数
async def setup_auto_vending_machines():
    try:
        # 自動配置設定を読み込み
        auto_config = load_auto_vending_config()
        
        if not auto_config:
            print("自販機自動配置設定がありません")
            return
        
        print("自販機自動配置を開始します")
        
        for config in auto_config:
            machine_id = config.get('id')
            channel_id = config.get('channel')
            
            if not machine_id or not channel_id:
                print(f"設定が不完全です: {config}")
                continue
            
            try:
                # チャンネルを取得
                channel = client.get_channel(int(channel_id))
                if not channel:
                    print(f"チャンネルが見つかりません: {channel_id}")
                    continue
                
                # チャンネルの投稿をすべて削除
                print(f"チャンネルをクリア中: {channel.name}")
                await clear_channel(channel)
                
                # 自販機情報を取得
                vending_machines = load_vending_machines()
                target_machine = None
                
                for machine in vending_machines.get("machines", []):
                    if machine.get("id") == machine_id:
                        target_machine = machine
                        break
                
                if not target_machine:
                    print(f"自販機が見つかりません: {machine_id}")
                    continue
                
                # 自販機の商品情報を取得
                all_stock = load_all_stock()
                machine_products = []
                
                for product_id in target_machine.get("products", []):
                    for product in all_stock.get("products", []):
                        if product["id"] == product_id:
                            # 在庫情報を取得
                            stock_data = load_product_stock(product_id)
                            product_info = {
                                "id": product["id"],
                                "name": product["name"],
                                "description": product["description"],
                                "price": product["price"],
                                "stock": stock_data.get("stock", 0)
                            }
                            machine_products.append(product_info)
                            break
                
                # 自販機の埋め込みメッセージを作成
                embed = discord.Embed(
                    title=f"🛒 {target_machine['name']}",
                    description=target_machine['description'],
                    color=0x3498db,
                    timestamp=discord.utils.utcnow()
                )
                
                # 商品一覧を追加
                if machine_products:
                    for product in machine_products:
                        # 在庫表示の処理
                        if product["stock"] == -1:
                            stock_display = "∞ (無限)"
                            stock_status = "✅ 在庫あり"
                        else:
                            stock_display = f"{product['stock']}個"
                            stock_status = "✅ 在庫あり" if product["stock"] > 0 else "❌ 売り切れ"
                        
                        embed.add_field(
                            name=f"📦 {product['name']} (¥{product['price']:,})",
                            value=f"📝 {product['description']}\n📊 在庫: {stock_display}\n{stock_status}\n🆔 `{product['id']}`",
                            inline=False
                        )
                else:
                    embed.add_field(
                        name="❌ 商品なし",
                        value="この自販機には商品が配置されていません。",
                        inline=False
                    )
                
                embed.add_field(
                    name="🏪 自販機情報",
                    value=f"🆔 **ID:** `{target_machine['id']}`\n📅 **作成日:** {target_machine['created_at'][:10]}",
                    inline=False
                )
                
                embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=channel.guild.icon.url if channel.guild.icon else None)
                
                # 購入ボタンのビューを作成（自動設置用はタイムアウトなし）
                purchase_view = AutoVendingPurchaseView(target_machine['id'], machine_products)
                
                # 自販機を配置
                await channel.send(embed=embed, view=purchase_view)
                print(f"自販機を配置しました: {machine_id} -> {channel.name}")
                
            except Exception as e:
                print(f"自販機配置エラー ({machine_id}): {e}")
        
        print("自販機自動配置が完了しました")
        
    except Exception as e:
        print(f"自販機自動配置でエラーが発生しました: {e}")

# チャンネルクリア関数
async def clear_channel(channel):
    try:
        # チャンネルの全メッセージを削除
        async for message in channel.history(limit=None):
            try:
                await message.delete()
            except discord.Forbidden:
                print(f"メッセージの削除権限がありません: {message.id}")
            except discord.NotFound:
                print(f"メッセージが見つかりません: {message.id}")
            except Exception as e:
                print(f"メッセージ削除でエラー: {e}")
    except Exception as e:
        print(f"チャンネルクリアでエラー: {e}")

# メンバーが参加した時の処理
@client.event
async def on_member_join(member):
    print(f"メンバー参加イベントが発火: {member.name} ({member.id})")
    
    # ウェルカムチャンネルのID（ここを実際のチャンネルIDに変更してください）
    welcome_channel_id = 1398005113527730376
    
    try:
        channel = client.get_channel(welcome_channel_id)
        if channel:
            print(f"ウェルカムチャンネルが見つかりました: {channel.name}")
            
            # 埋め込みメッセージを作成
            embed = discord.Embed(
                title="🎉 新たなメンバーの参戦！",
                description=f"**{member.name}** が我が軍に加わった！",
                color=0x00ff00,  # 緑色
                timestamp=discord.utils.utcnow()
            )
            
            # ユーザーのアバターを設定
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            
            # フィールドを追加
            embed.add_field(
                name="👤 アカウント情報",
                value=f"**ユーザー名:** {member.name}\n**表示名:** {member.display_name}",
                inline=False
            )
            
            embed.add_field(
                name="🎯 サーバー情報",
                value=f"**参加日:** {member.joined_at.strftime('%Y年%m月%d日 %H:%M')}\n**メンバー数:** {member.guild.member_count}人目",
                inline=False
            )
            
            # フッターを追加
            embed.set_footer(text=f"†NEO睡眠†へようこそ！", icon_url=member.guild.icon.url if member.guild.icon else None)
            
            await channel.send(embed=embed)
            print(f"ウェルカムメッセージを送信しました: {member.name}")
        else:
            print(f"ウェルカムチャンネルが見つかりません: {welcome_channel_id}")
    except Exception as e:
        print(f"ウェルカムメッセージの送信でエラーが発生しました: {e}")
        print(f"エラーの詳細: {type(e).__name__}")

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    
    # 管理者権限チェック
    if not message.author.guild_permissions.administrator:
        return

    # 在庫追加待機中のユーザーかチェック
    stock_waiting_users = getattr(client, 'stock_waiting_users', {})
    if message.author.id in stock_waiting_users:
        waiting_info = stock_waiting_users[message.author.id]
        # タイムアウトチェック（5分）
        if datetime.now().timestamp() - waiting_info['timestamp'] > 300:
            del stock_waiting_users[message.author.id]
            return
        try:
            lines = message.content.strip().split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            product_id = waiting_info['product_id']
            current_stock_data = load_product_stock(product_id)
            # 無限在庫化の場合
            if current_stock_data.get('stock', 0) == -1:
                if len(lines) != 1:
                    await message.reply('❌ 無限在庫化時は1行だけ入力してください。')
                    del stock_waiting_users[message.author.id]
                    return
                # dataを1件だけに上書き
                current_stock_data['data'] = [lines[0]]
                save_product_stock(product_id, -1, current_stock_data['data'])
                embed = discord.Embed(
                    title="✅ 無限在庫データ更新完了",
                    description=f"商品: **{waiting_info['product_name']}**",
                    color=0x00ff00,
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="🆔 商品ID", value=product_id, inline=True)
                embed.add_field(name="📝 データ内容", value=lines[0], inline=False)
                embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=message.guild.icon.url if message.guild.icon else None)
                await message.reply(embed=embed)
                del stock_waiting_users[message.author.id]
                return
            # 通常の在庫追加
            if len(lines) != waiting_info['expected_count']:
                await message.reply(f'❌ 期待される行数と一致しません。期待: {waiting_info["expected_count"]}行、実際: {len(lines)}行')
                return
            # dataに後ろから追加
            if 'data' not in current_stock_data:
                current_stock_data['data'] = []
            for line in lines:
                current_stock_data['data'].append(line)
            save_product_stock(product_id, current_stock_data['stock'], current_stock_data['data'])
            embed = discord.Embed(
                title="✅ 商品データ追加完了",
                description=f"商品: **{waiting_info['product_name']}**",
                color=0x00ff00,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="🆔 商品ID", value=product_id, inline=True)
            embed.add_field(name="📊 追加されたデータ数", value=f"{len(lines)}個", inline=True)
            embed.add_field(name="📝 総データ数", value=f"{len(current_stock_data['data'])}個", inline=True)
            embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=message.guild.icon.url if message.guild.icon else None)
            await message.reply(embed=embed)
            del stock_waiting_users[message.author.id]
        except Exception as e:
            await message.reply(f'❌ 商品データの追加中にエラーが発生しました: {e}')
            del stock_waiting_users[message.author.id]

    # チケットシステムコマンド
    elif message.content == 'k!ticket':
        # 管理者権限チェック
        if not message.author.guild_permissions.administrator:
            await message.channel.send('❌ このコマンドは管理者のみ使用できます。')
            return
        
        # チケット作成用の埋め込みメッセージ
        embed = discord.Embed(
            title="🎫 ticket",
            description="お問い合わせ/自販機以外の商品購入はこちらから",
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        
        # チケット作成ボタンのビューを作成
        ticket_view = TicketCreateView()
        
        await message.channel.send(embed=embed, view=ticket_view)
    

    
    # 認証パネル作成コマンド
    elif message.content == 'k!verify':
        # 管理者権限チェック
        if not message.author.guild_permissions.administrator:
            await message.channel.send('❌ このコマンドは管理者のみ使用できます。')
            return
        
        # 認証パネル用の埋め込みメッセージ
        embed = discord.Embed(
            title="🔐 認証パネル",
            description="下のボタンを押して認証を完了してください。",
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        
        # 指定された画像を設定
        embed.set_image(url="https://cdn.discordapp.com/attachments/1398334731564748981/1398335054769557625/4577af4641060ee401cc2897e9fc9118.jpg?ex=6884fc80&is=6883ab00&hm=7d6982419819f961391baef08ce499024f9564a9f6bd9648612946c6e937eab0&")
        
        embed.set_footer(text="†NEO睡眠† 認証システム", icon_url=message.guild.icon.url if message.guild.icon else None)
        
        # 認証ボタンのビューを作成
        verify_view = VerificationPanelView()
        
        await message.channel.send(embed=embed, view=verify_view)
        await message.channel.send("✅ 認証パネルを作成しました！")
    
    # キックコマンド（管理者専用）
    elif message.content.startswith('k!kick'):
        if not message.author.guild_permissions.administrator:
            await message.channel.send('❌ 誰がお前なんかに従うかばぁぁぁぁかwwwwwwwwwww')
            return
        
        if not message.guild.me.guild_permissions.kick_members:
            await message.channel.send('❌ キックする権限をよこせ。')
            return
        
        if len(message.mentions) == 0:
            await message.channel.send('❌ 誰を斬るのか言え。')
            return
        
        target_user = message.mentions[0]
        
        # 自分自身をキックできないようにする
        if target_user == message.author:
            await message.channel.send('❌ 自殺は王にゃ似合わない。')
            return
        
        # ボットをキックできないようにする
        if target_user == message.guild.me:
            await message.channel.send('❌ 機械なんか斬ってもおもんないぜ。')
            return
        
        try:
            await target_user.kick(reason=f"管理者 {message.author.name} の命令を承った。")
            await message.channel.send(f'✅ {target_user.name} を終了した。')
        except discord.Forbidden:
            await message.channel.send('❌ 権限が不足しています。ボットの権限を確認してください。')
        except Exception as e:
            await message.channel.send(f'❌ エラーが発生しました: {e}')
    
    # BANコマンド（管理者専用）
    elif message.content.startswith('k!ban'):
        if not message.author.guild_permissions.administrator:
            await message.channel.send('❌ 俺がお前に従う義理はない。')
            return
        
        if len(message.mentions) == 0:
            await message.channel.send('❌ 誰を斬るのか言え。')
            return
        
        target_user = message.mentions[0]
        
        # 自分自身をBANできないようにする
        if target_user == message.author:
            await message.channel.send('❌ 自滅は王にゃ似合わない。')
            return
        
        # ボットをBANできないようにする
        if target_user == message.guild.me:
            await message.channel.send('❌ めんどい。')
            return
        
        try:
            await target_user.ban(reason=f"管理者 {message.author.name} の依頼により")
            await message.channel.send(f'✅ {target_user.name} を殺害した。')
        except discord.Forbidden:
            await message.channel.send('❌ 権限が不足しています。ボットの権限を確認してください。')
        except Exception as e:
            await message.channel.send(f'❌ エラーが発生しました: {e}')
    
    # 自販機商品追加コマンド
    elif message.content.startswith('/kwtkzk add'):
        # 管理者権限チェック
        if not message.author.guild_permissions.administrator:
            await message.channel.send('❌ このコマンドは管理者のみ使用できます。')
            return
        
        try:
            # コマンドからパラメータを抽出
            content = message.content.replace('/kwtkzk add', '').strip()
            parts = content.split()
            
            if len(parts) < 4:
                await message.channel.send('❌ パラメータが不足しています。\n使用方法: `/kwtkzk add 商品名 説明 初期在庫 値段 [ID]`\n例: `/kwtkzk add コーラ 炭酸飲料 10 150 coke`')
                return
            
            # パラメータを解析
            product_name = parts[0]
            description = parts[1]
            initial_stock = int(parts[2])
            price = int(parts[3])
            product_id = parts[4] if len(parts) > 4 else product_name.lower().replace(' ', '_')
            
            # 全商品情報を読み込み
            all_stock = load_all_stock()
            
            # 商品IDの重複チェック
            for product in all_stock["products"]:
                if product["id"] == product_id:
                    await message.channel.send(f'❌ 商品ID `{product_id}` は既に使用されています。')
                    return
            
            # 新しい商品を追加
            new_product = {
                "id": product_id,
                "name": product_name,
                "description": description,
                "price": price,
                "created_at": datetime.now().isoformat()
            }
            
            all_stock["products"].append(new_product)
            save_all_stock(all_stock)
            
            # 在庫ファイルを作成
            save_product_stock(product_id, initial_stock)
            
            # 成功メッセージを作成
            embed = discord.Embed(
                title="✅ 商品追加完了",
                description=f"商品ID: `{product_id}`",
                color=0x00ff00,
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="📦 商品名",
                value=product_name,
                inline=True
            )
            
            embed.add_field(
                name="📝 説明",
                value=description,
                inline=True
            )
            
            embed.add_field(
                name="💰 価格",
                value=f"¥{price:,}",
                inline=True
            )
            
            embed.add_field(
                name="📊 初期在庫",
                value=f"{initial_stock}個",
                inline=True
            )
            
            embed.add_field(
                name="🆔 商品ID",
                value=product_id,
                inline=True
            )
            
            embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=message.guild.icon.url if message.guild.icon else None)
            
            await message.channel.send(embed=embed)
            
        except ValueError:
            await message.channel.send('❌ 在庫数と価格は数字で入力してください。')
        except Exception as e:
            await message.channel.send(f'❌ エラーが発生しました: {e}')
    
    # 自販機作成コマンド
    elif message.content.startswith('/kwtkzk vending'):
        # 管理者権限チェック
        if not message.author.guild_permissions.administrator:
            await message.channel.send('❌ このコマンドは管理者のみ使用できます。')
            return
        
        try:
            # コマンドからパラメータを抽出
            content = message.content.replace('/kwtkzk vending', '').strip()
            parts = content.split()
            
            if len(parts) < 3:
                await message.channel.send('❌ パラメータが不足しています。\n使用方法: `/kwtkzk vending 自販機の名前 自販機の説明 商品ID1 商品ID2 ...`\n例: `/kwtkzk vending 1階自販機 飲み物とスナック coke chips`')
                return
            
            # パラメータを解析
            machine_name = parts[0]
            machine_description = parts[1]
            product_ids = parts[2:]
            
            # 全商品情報を読み込み
            all_stock = load_all_stock()
            available_products = [p["id"] for p in all_stock["products"]]
            
            # 商品IDの存在確認
            invalid_products = []
            valid_products = []
            for product_id in product_ids:
                if product_id in available_products:
                    valid_products.append(product_id)
                else:
                    invalid_products.append(product_id)
            
            if invalid_products:
                await message.channel.send(f'❌ 以下の商品IDが存在しません: {", ".join(invalid_products)}\n利用可能な商品ID: {", ".join(available_products)}')
                return
            
            if not valid_products:
                await message.channel.send('❌ 有効な商品が指定されていません。')
                return
            
            # 自販機一覧を読み込み
            vending_machines = load_vending_machines()
            
            # 自販機IDを生成（名前ベース）
            machine_id = machine_name.lower().replace(' ', '_').replace('　', '_')
            
            # 自販機IDの重複チェック
            for machine in vending_machines["machines"]:
                if machine["id"] == machine_id:
                    await message.channel.send(f'❌ 自販機名 `{machine_name}` は既に使用されています。')
                    return
            
            # 新しい自販機を追加
            new_machine = {
                "id": machine_id,
                "name": machine_name,
                "description": machine_description,
                "products": valid_products,
                "created_at": datetime.now().isoformat(),
                "created_by": message.author.id
            }
            
            vending_machines["machines"].append(new_machine)
            save_vending_machines(vending_machines)
            
            # 成功メッセージを作成
            embed = discord.Embed(
                title="🛒 自販機作成完了",
                description=f"自販機ID: `{machine_id}`",
                color=0x00ff00,
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="🏪 自販機名",
                value=machine_name,
                inline=True
            )
            
            embed.add_field(
                name="📝 説明",
                value=machine_description,
                inline=True
            )
            
            embed.add_field(
                name="📦 配置商品",
                value="\n".join([f"• {pid}" for pid in valid_products]),
                inline=False
            )
            
            embed.add_field(
                name="🆔 自販機ID",
                value=machine_id,
                inline=True
            )
            
            embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=message.guild.icon.url if message.guild.icon else None)
            
            await message.channel.send(embed=embed)
            
        except Exception as e:
            await message.channel.send(f'❌ エラーが発生しました: {e}')
    
    # 既存のコマンド
    elif message.content == 'k!oi':
        await message.channel.send('ｶﾜﾀﾀﾞﾖ!')

# 自販機システムの関数
def load_all_stock():
    """全商品の在庫情報を読み込む"""
    try:
        with open('stock/AllStock.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"products": []}

def save_all_stock(data):
    """全商品の在庫情報を保存"""
    os.makedirs('stock', exist_ok=True)
    with open('stock/AllStock.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_product_stock(product_id):
    """特定商品の在庫数を読み込む"""
    try:
        with open(f'stock/{product_id}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"stock": 0}

def save_product_stock(product_id, stock_count, data=None):
    """特定商品の在庫数を保存"""
    os.makedirs('stock', exist_ok=True)
    obj = {"stock": stock_count}
    if data is not None:
        obj["data"] = data
    else:
        # 既存dataがあれば維持
        try:
            with open(f'stock/{product_id}.json', 'r', encoding='utf-8') as f:
                old = json.load(f)
                if 'data' in old:
                    obj['data'] = old['data']
        except Exception:
            pass
    with open(f'stock/{product_id}.json', 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_vending_machines():
    """自販機一覧を読み込む"""
    try:
        with open('stock/vending_machines.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"machines": []}

def save_vending_machines(data):
    """自販機一覧を保存"""
    os.makedirs('stock', exist_ok=True)
    with open(f'stock/vending_machines.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_auto_vending_config():
    """自販機自動配置設定を読み込む"""
    try:
        with open('stock/auto_vending_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_auto_vending_config(data):
    """自販機自動配置設定を保存"""
    os.makedirs('stock', exist_ok=True)
    with open('stock/auto_vending_config.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



# スラッシュコマンドの定義
@tree.command(name="kwtkzk-add", description="自販機に商品を追加")
@app_commands.describe(
    product_name="商品名",
    description="商品の説明",
    price="価格（円）",
    product_id="商品ID（任意の英数字）"
)
async def kwtkzk_add(interaction: discord.Interaction, product_name: str, description: str, price: int, product_id: str):
    # 管理者権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('❌ このコマンドは管理者のみ使用できます。', ephemeral=True)
        return
    
    try:
        # 全商品情報を読み込み
        all_stock = load_all_stock()
        
        # 商品IDの重複チェック
        for product in all_stock["products"]:
            if product["id"] == product_id:
                await interaction.response.send_message(f'❌ 商品ID `{product_id}` は既に使用されています。', ephemeral=True)
                return
        
        # 新しい商品を追加
        new_product = {
            "name": product_name,
            "description": description,
            "price": price,
            "id": product_id,
            "created_at": datetime.now().isoformat()
        }
        
        all_stock["products"].append(new_product)
        save_all_stock(all_stock)
        
        # 在庫ファイルを作成（初期在庫は0個）
        save_product_stock(product_id, 0)
        
        # 成功メッセージを作成
        embed = discord.Embed(
            title="✅ 商品追加完了",
            description=f"商品ID: `{product_id}`",
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        

        
        embed.add_field(name="📦 商品名", value=product_name, inline=True)
        embed.add_field(name="📝 説明", value=description, inline=True)
        embed.add_field(name="💰 価格", value=f"¥{price:,}", inline=True)
        embed.add_field(name="📊 初期在庫", value="0個", inline=True)
        embed.add_field(name="🆔 商品ID", value=product_id, inline=True)
        embed.add_field(name="💡 使用方法", value=f"自販機作成時は `{product_id}` を使用してください", inline=False)
        embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        await interaction.response.send_message(f'❌ エラーが発生しました: {e}', ephemeral=True)

@tree.command(name="kwtkzk-stock", description="商品の在庫を管理")
@app_commands.describe(
    product_id="商品ID",
    add_stock="追加する在庫数（-1で無限在庫化）"
)
async def kwtkzk_stock(interaction: discord.Interaction, product_id: str, add_stock: int):
    # 管理者権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('❌ このコマンドは管理者のみ使用できます。', ephemeral=True)
        return
    
    try:
        # 全商品情報を読み込み
        all_stock = load_all_stock()
        
        # 商品IDの存在確認
        product_exists = False
        for product in all_stock["products"]:
            if product["id"] == product_id:
                product_exists = True
                product_name = product["name"]
                break
        
        if not product_exists:
            await interaction.response.send_message(f'❌ 商品ID `{product_id}` が見つかりません。', ephemeral=True)
            return
        
        # 現在の在庫情報を読み込み
        current_stock_data = load_product_stock(product_id)
        
        # 在庫数を更新
        if add_stock == -1:
            # 無限在庫化
            current_stock_data["stock"] = -1
            stock_message = "∞ (無限)"
        else:
            # 在庫を追加
            if current_stock_data["stock"] == -1:
                current_stock_data["stock"] = add_stock
            else:
                current_stock_data["stock"] += add_stock
            stock_message = f"{current_stock_data['stock']}個"
        
        # 在庫情報を保存
        save_product_stock(product_id, current_stock_data["stock"])
        
        # 成功メッセージを作成
        embed = discord.Embed(
            title="✅ 在庫更新完了",
            description=f"商品: **{product_name}**",
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="🆔 商品ID", value=product_id, inline=True)
        embed.add_field(name="📊 現在の在庫", value=stock_message, inline=True)
        embed.add_field(name="➕ 追加数", value=f"{add_stock}個" if add_stock != -1 else "無限在庫化", inline=True)
        
        if add_stock > 0:
            embed.add_field(name="📝 次のステップ", value="商品データを追加するには、改行区切りでメッセージを送信してください。", inline=False)
        
        embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message(embed=embed)
        
        # 商品データ追加のための待機状態を設定
        if add_stock > 0:
            # ユーザーIDと商品IDを保存して、次のメッセージを待機
            interaction.client.stock_waiting_users = getattr(interaction.client, 'stock_waiting_users', {})
            interaction.client.stock_waiting_users[interaction.user.id] = {
                'product_id': product_id,
                'product_name': product_name,
                'expected_count': add_stock,
                'timestamp': datetime.now().timestamp()
            }
        
    except Exception as e:
        await interaction.response.send_message(f'❌ エラーが発生しました: {e}', ephemeral=True)

@tree.command(name="kwtkzk-vending", description="自販機を作成")
@app_commands.describe(
    machine_name="自販機の名前",
    machine_description="自販機の説明",
    product_ids="商品ID（スペース区切りで複数指定可能）",
    machine_id="自販機ID（任意）"
)
async def kwtkzk_vending(interaction: discord.Interaction, machine_name: str, machine_description: str, product_ids: str, machine_id: str = None):
    # 管理者権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('❌ このコマンドは管理者のみ使用できます。', ephemeral=True)
        return
    
    try:
        # 商品IDを分割
        product_id_list = product_ids.split()
        
        # 全商品情報を読み込み
        all_stock = load_all_stock()
        available_products = [p["id"] for p in all_stock["products"]]
        
        # 商品IDの存在確認
        invalid_products = []
        valid_products = []
        for product_id in product_id_list:
            if product_id in available_products:
                valid_products.append(product_id)
            else:
                invalid_products.append(product_id)
        
        if invalid_products:
            await interaction.response.send_message(f'❌ 以下の商品IDが存在しません: {", ".join(invalid_products)}\n利用可能な商品ID: {", ".join(available_products)}', ephemeral=True)
            return
        
        if not valid_products:
            await interaction.response.send_message('❌ 有効な商品が指定されていません。', ephemeral=True)
            return
        
        # 自販機一覧を読み込み
        vending_machines = load_vending_machines()
        
        # 自販機IDの処理
        if not machine_id:
            # 自販機IDが指定されていない場合、自動生成
            machine_id = machine_name.lower().replace(' ', '_').replace('　', '_')
        else:
            # 自販機IDが指定されている場合、そのまま使用
            machine_id = machine_id.lower().replace(' ', '_').replace('　', '_')
        
        # 自販機IDの重複チェック
        for machine in vending_machines["machines"]:
            if machine["id"] == machine_id:
                await interaction.response.send_message(f'❌ 自販機ID `{machine_id}` は既に使用されています。', ephemeral=True)
                return
        
        # 新しい自販機を追加
        new_machine = {
            "id": machine_id,
            "name": machine_name,
            "description": machine_description,
            "products": valid_products,
            "created_at": datetime.now().isoformat(),
            "created_by": interaction.user.id
        }
        
        vending_machines["machines"].append(new_machine)
        save_vending_machines(vending_machines)
        
        # 成功メッセージを作成
        embed = discord.Embed(
            title="🛒 自販機作成完了",
            description=f"自販機ID: `{machine_id}`",
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="🏪 自販機名", value=machine_name, inline=True)
        embed.add_field(name="📝 説明", value=machine_description, inline=True)
        embed.add_field(name="📦 配置商品", value="\n".join([f"• {pid}" for pid in valid_products]), inline=False)
        embed.add_field(name="🆔 自販機ID", value=machine_id, inline=True)
        embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        await interaction.response.send_message(f'❌ エラーが発生しました: {e}', ephemeral=True)

@tree.command(name="kwtkzk-summon", description="自販機を呼び出す")
@app_commands.describe(
    machine_id="自販機のID"
)
async def kwtkzk_summon(interaction: discord.Interaction, machine_id: str):
    try:
        # 自販機一覧を読み込み
        vending_machines = load_vending_machines()
        all_stock = load_all_stock()
        
        # 指定された自販機を検索
        target_machine = None
        for machine in vending_machines["machines"]:
            if machine["id"] == machine_id:
                target_machine = machine
                break
        
        if not target_machine:
            available_machines = [m["id"] for m in vending_machines["machines"]]
            await interaction.response.send_message(f'❌ 自販機ID `{machine_id}` が見つかりません。\n利用可能な自販機ID: {", ".join(available_machines) if available_machines else "なし"}', ephemeral=True)
            return
        
        # 自販機の商品情報を取得
        product_info = []
        for product_id in target_machine["products"]:
            product = next((p for p in all_stock["products"] if p["id"] == product_id), None)
            if product:
                stock_data = load_product_stock(product_id)
                current_stock = stock_data["stock"]
                product_info.append({
                    "id": product_id,
                    "name": product["name"],
                    "description": product["description"],
                    "price": product["price"],
                    "stock": current_stock
                })
        
        # 自販機の埋め込みメッセージを作成
        embed = discord.Embed(
            title=f"🛒 {target_machine['name']}",
            description=target_machine['description'],
            color=0x3498db,
            timestamp=discord.utils.utcnow()
        )
        
        # 商品一覧を追加
        if product_info:
            for product in product_info:
                # 在庫表示の処理
                if product["stock"] == -1:
                    stock_display = "∞ (無限)"
                    stock_status = "✅ 在庫あり"
                else:
                    stock_display = f"{product['stock']}個"
                    stock_status = "✅ 在庫あり" if product["stock"] > 0 else "❌ 売り切れ"
                
                embed.add_field(
                    name=f"📦 {product['name']} (¥{product['price']:,})",
                    value=f"📝 {product['description']}\n📊 在庫: {stock_display}\n{stock_status}\n🆔 `{product['id']}`",
                    inline=False
                )
        else:
            embed.add_field(
                name="❌ 商品なし",
                value="この自販機には商品が配置されていません。",
                inline=False
            )
        
        embed.add_field(
            name="🏪 自販機情報",
            value=f"🆔 **ID:** `{target_machine['id']}`\n📅 **作成日:** {target_machine['created_at'][:10]}",
            inline=False
        )
        
        embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        # 購入ボタンを追加
        purchase_view = PurchaseView(machine_id, product_info)
        await interaction.response.send_message(embed=embed, view=purchase_view)
        
    except Exception as e:
        await interaction.response.send_message(f'❌ エラーが発生しました: {e}', ephemeral=True)

# 自動設置用の購入ボタンビュー（タイムアウトなし）
class AutoVendingPurchaseView(View):
    def __init__(self, machine_id: str, products: list):
        super().__init__(timeout=None)  # タイムアウトなし
        self.machine_id = machine_id
        self.products = products
    
    @discord.ui.button(label="購入する", style=ButtonStyle.green, emoji="🛒")
    async def purchase(self, interaction: discord.Interaction, button: Button):
        # 購入セレクトメニューを表示
        purchase_view = PurchaseSelectView(self.machine_id, self.products)
        await interaction.response.send_message("🛒 購入したい商品を選択してください:", view=purchase_view, ephemeral=True)

# 購入用のボタンビュー（手動呼び出し用）
class PurchaseView(View):
    def __init__(self, machine_id: str, products: list):
        super().__init__(timeout=300)  # 5分でタイムアウト
        self.machine_id = machine_id
        self.products = products
    
    @discord.ui.button(label="購入する", style=ButtonStyle.green, emoji="🛒")
    async def purchase(self, interaction: discord.Interaction, button: Button):
        # 購入セレクトメニューを表示
        purchase_view = PurchaseSelectView(self.machine_id, self.products)
        await interaction.response.send_message("🛒 購入したい商品を選択してください:", view=purchase_view, ephemeral=True)

# 自動設置用の購入セレクトメニュー（タイムアウトなし）
class AutoVendingPurchaseSelectView(View):
    def __init__(self, machine_id: str, products: list):
        super().__init__(timeout=None)  # タイムアウトなし
        self.machine_id = machine_id
        self.products = products
        
        # 商品選択用のセレクトメニューを作成
        options = []
        for product in products:
            if product["stock"] == -1:
                stock_display = "∞ (無限)"
            else:
                stock_display = f"{product['stock']}個"
            
            options.append(discord.SelectOption(
                label=f"{product['name']} - ¥{product['price']:,}",
                description=f"在庫: {stock_display} | {product['description'][:50]}...",
                value=product["id"]
            ))
        
        self.add_item(ProductSelect(options))
        self.add_item(QuantityInput())

# 購入用のセレクトメニュー（手動呼び出し用）
class PurchaseSelectView(View):
    def __init__(self, machine_id: str, products: list):
        super().__init__(timeout=300)  # 5分でタイムアウト
        self.machine_id = machine_id
        self.products = products
        
        # 商品選択用のセレクトメニューを作成
        options = []
        for product in products:
            if product["stock"] == -1:
                stock_display = "∞ (無限)"
            else:
                stock_display = f"{product['stock']}個"
            
            options.append(discord.SelectOption(
                label=f"{product['name']} - ¥{product['price']:,}",
                description=f"在庫: {stock_display} | {product['description'][:50]}...",
                value=product["id"]
            ))
        
        self.add_item(ProductSelect(options))
        self.add_item(QuantityInput())

# 商品選択用のセレクトメニュー
class ProductSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder="購入したい商品を選択してください",
            options=options,
            min_values=1,
            max_values=1
        )
        self.selected_product = None
    
    async def callback(self, interaction: discord.Interaction):
        self.selected_product = self.values[0]
        await interaction.response.send_message(f"✅ 商品を選択しました: {self.selected_product}", ephemeral=True)

# 数量入力用のボタン
class QuantityInput(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="数量を入力",
            style=discord.ButtonStyle.primary,
            emoji="📝"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # 選択された商品を取得
        selected_product = None
        for item in self.view.children:
            if isinstance(item, ProductSelect) and item.selected_product:
                selected_product = item.selected_product
                break
        
        if not selected_product:
            await interaction.response.send_message("❌ 先に商品を選択してください。", ephemeral=True)
            return
        
        # 数量入力用のモーダルを表示
        await interaction.response.send_modal(QuantityModal(selected_product))

# 数量入力用のモーダル
class QuantityModal(discord.ui.Modal, title="購入数量入力"):
    def __init__(self, selected_product: str):
        super().__init__()
        self.selected_product = selected_product
        
        self.quantity = discord.ui.TextInput(
            label="購入数量",
            placeholder="購入する数量を入力してください",
            required=True,
            max_length=3
        )
        
        self.add_item(self.quantity)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            quantity = int(self.quantity.value)
            
            if quantity <= 0:
                await interaction.response.send_message("❌ 購入数量は1以上で入力してください。", ephemeral=True)
                return
            
            # 商品情報を取得
            all_stock = load_all_stock()
            target_product = None
            for product in all_stock["products"]:
                if product["id"] == self.selected_product:
                    target_product = product
                    break
            
            if not target_product:
                await interaction.response.send_message("❌ 商品情報が見つかりません。", ephemeral=True)
                return
            
            # 在庫チェック
            stock_data = load_product_stock(self.selected_product)
            current_stock = stock_data["stock"]
            
            if current_stock != -1 and current_stock < quantity:
                await interaction.response.send_message(f"❌ 在庫が不足しています。現在の在庫: {current_stock}個", ephemeral=True)
                return
            
            # 合計金額計算
            total_price = target_product["price"] * quantity
            
            # 購入者に受け取りリンクを送信
            try:
                user = interaction.user
                
                # 受け取りリンク作成用の埋め込みメッセージ
                payment_embed = discord.Embed(
                    title="💳 支払い手順",
                    description="以下の手順で支払いを完了してください。",
                    color=0x3498db,
                    timestamp=discord.utils.utcnow()
                )
                
                payment_embed.add_field(name="📦 商品名", value=target_product['name'], inline=True)
                payment_embed.add_field(name="📊 数量", value=f"{quantity}個", inline=True)
                payment_embed.add_field(name="💰 単価", value=f"¥{target_product['price']:,}", inline=True)
                payment_embed.add_field(name="💵 合計金額", value=f"¥{total_price:,}", inline=True)
                payment_embed.add_field(
                    name="📋 支払い手順", 
                    value="1. PayPayアプリで受け取りリンクを作成\n2. 金額を **¥" + f"{total_price:,}" + "** に設定\n3. パスワードは任意で設定\n4. 下のボタンを押してリンクを入力\n5. 支払い確認後、商品データをDMで送信します", 
                    inline=False
                )
                
                payment_embed.set_footer(text="†NEO睡眠† 自販機システム")
                
                # 購入情報を一時保存（後で支払い確認時に使用）
                purchase_info = {
                    "user_id": interaction.user.id,
                    "product_id": self.selected_product,
                    "quantity": quantity,
                    "total_price": total_price,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 購入情報をファイルに保存
                purchase_file = f'stock/purchase_{interaction.user.id}_{int(datetime.now().timestamp())}.json'
                os.makedirs('stock', exist_ok=True)
                with open(purchase_file, 'w', encoding='utf-8') as f:
                    json.dump(purchase_info, f, ensure_ascii=False, indent=2)
                
                # 支払いリンク入力ボタンのビューを作成
                payment_view = PaymentLinkView(purchase_file)
                
                await interaction.response.send_message(embed=payment_embed, view=payment_view, ephemeral=True)
                
            except Exception as e:
                await interaction.response.send_message(f"❌ 支払い手順の送信に失敗しました: {e}", ephemeral=True)
                
        except ValueError:
            await interaction.response.send_message("❌ 購入数量は数字で入力してください。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ エラーが発生しました: {e}", ephemeral=True)

# 支払いリンク入力用のボタンビュー
class PaymentLinkView(View):
    def __init__(self, purchase_file: str):
        super().__init__(timeout=300)  # 5分でタイムアウト
        self.purchase_file = purchase_file
    
    @discord.ui.button(label="支払いリンクを入力", style=ButtonStyle.primary, emoji="💳")
    async def input_payment_link(self, interaction: discord.Interaction, button: Button):
        # 支払いリンク入力用のモーダルを表示
        await interaction.response.send_modal(PaymentLinkModal(self.purchase_file))

# 支払いリンク入力用のモーダル
class PaymentLinkModal(discord.ui.Modal, title="PayPay支払いリンク入力"):
    def __init__(self, purchase_file: str):
        super().__init__()
        self.purchase_file = purchase_file
        
        self.payment_link = discord.ui.TextInput(
            label="PayPay受け取りリンク",
            placeholder="https://pay.paypay.ne.jp/...",
            required=True,
            max_length=200
        )
        
        self.password = discord.ui.TextInput(
            label="パスワード（必要な場合）",
            placeholder="パスワードが設定されている場合は入力してください",
            required=False,
            max_length=10
        )
        
        self.add_item(self.payment_link)
        self.add_item(self.password)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            paypay_url = self.payment_link.value.strip()
            
            # URLの形式チェック
            if not paypay_url.startswith("https://pay.paypay.ne.jp/"):
                await interaction.response.send_message("❌ 有効なPayPayリンクではありません。", ephemeral=True)
                return
            
            # 購入情報を読み込み
            try:
                with open(self.purchase_file, 'r', encoding='utf-8') as f:
                    purchase_info = json.load(f)
            except FileNotFoundError:
                await interaction.response.send_message("❌ 購入情報が見つかりません。", ephemeral=True)
                return
            
            # PayPayリンクの金額を確認
            try:
                paypay = PayPay(access_token="ICAgeyJraWQiOiJ1bS1qd2Utajd2OEVJZ08xeGRkUTQzNHh1VE5WSmE4WHplRks1dUEiLCJ0eXAiOiJydCtqd3QiLCJlbmMiOiJBMjU2R0NNIiwidGFnIjoiT3ctLVcyY3dOUG9rb1I1eHpPUGlDdyIsImFsZyI6IkEyNTZHQ01LVyIsIml2IjoiQVhKcXhiSWpWR3c3WFQxTSJ9~TjmkKbrU6tL2Lu2Zls-Zc9HGtYB-c6lbyGyoD16kM6g~ore8xB95M-xTkr1w~OSt6IEwWa6oefu47AOtx0xP6Y1uvZ8xeL3mJl4sAAkYQ3mbrS5xPnPYAIQsVspyRqBIL5Wd-nG5CDNjZtrNX7yW8fuFciBQyuXrue89w3f8JxdYCLrjCcRNhuTu_3b5-VAiKwqmbP2qvfyKeyPsK8__YR1AWe5j0YLT816nO6AIIjWxqPbX93EjD2faDCabdHNJEsNqPHI7Zc7DkfqDg5C_8LIqRjfOPl6HyddqpOQ3W9FAqeVUwVjH7DlJYeSkxnalSOTvBhtwFr77SkLnRRF6TddGQRKTQyC3HM8_u9mVPiR2UhV3Rwk9-MMt7hNGouj0ReKPgD4f4gz1hw-VAv1M-Y02k3mXv7aOoYQVhVFZsGNnrNxt-6hMxTGkFFdpv1rrkmU6mvz-SxhIhle4MTKC2DAIrRGIa3tprq1pIhiB1sDb7mjBsWXmqFXKM98a9mFZTkgfY0RFNAMWS9Tl1fvCyIkymY2wqzCfuY9jD89Fvj1KHpnls21t-8QhZfAKT_qO1e8jj4Ix4ZRqnijcuuBMaJYYBUIoUcRzGmAQQnpzXF7xqS7GARCGDY0xlyQpX2DgTualReSmNmvGK0DNvcV_Jh4Nhwq0rOK0-yKlgivvKW4Hm-lDePIC88LgFpLTNHfqcaP5eB3EdZMtrNgVZdxuJHNbtg0Dgdwrl5-fVVukpL6nvSsFdJ29jAhKNAkRvfc3T5Hy7dPxRiJ1frOqzccAWIzAWmJIb49UM8Bh1xj1YX_ZmG7xvaj3qxlNeaUJQ7iKgb8arF3F3xXTH5s0BezqXJrWSenoLIBgvH0L5ctgt4jg6JffyTxl1B2V_fgMpJabFzJz_pjZaVJJdC2TfsF5vlZ5lEXdMGiQFt9HrhhWc9vHgH3CZG2u4aUu1WzOte-mydRXfElUalFuZ_0oIzMx0uyNv4vumF7iY7GhjoCuAf9jvasyJCEZzYPWB5Vn1hHBo2lIMpuwDZvguhFrJdcdQrt30K7dMmI9jIadYPVk4TyfG3N_JkAko37O0AkEUGb1JoWnVZJu-1vbYuectgxtnMS2XswUmxLxFR_wtQHfbKAgAUZ88L0NJTtUEStak_2KB070d6UZK5iOFxLr6NB41HYW3DLMUfy8vjYjR0gxUQmfwZi847hfQPDHQnMXO9iAyofCDToKay6gR2WOL0yJTz10Oqz9IB-0biIde-dqkiHl8z1caYhi8A0zIcCEY52CGLrxxkU3t5eprawizOT7dK6gs_qVQqaCd~v2KLZNC6n864QMuiuIZPBQ")
                
                # リンクの金額を確認（PayPaythonのlink_checkメソッドを使用）
                link_info = paypay.link_check(paypay_url)
                
                # デバッグ情報を出力
                print(f"link_info type: {type(link_info)}")
                print(f"link_info content: {link_info}")
                
                # link_infoが辞書形式の場合の処理
                if isinstance(link_info, dict):
                    link_amount = link_info.get('amount', 0)
                    link_status = link_info.get('status', 'UNKNOWN')
                else:
                    # オブジェクト形式の場合
                    link_amount = getattr(link_info, 'amount', 0)
                    link_status = getattr(link_info, 'status', 'UNKNOWN')
                
                print(f"link_amount: {link_amount}")
                print(f"link_status: {link_status}")
                
                # リンクの状態をチェック
                if link_status != "PENDING":
                    await interaction.response.send_message(f"❌ リンクの状態が不正です。\n現在の状態: {link_status}\n期待状態: PENDING", ephemeral=True)
                    return
                
                if link_amount != purchase_info["total_price"]:
                    await interaction.response.send_message(f"❌ 金額が一致しません。\n期待金額: ¥{purchase_info['total_price']:,}\nリンク金額: ¥{link_amount:,}", ephemeral=True)
                    return
                
                # 支払いを受け取る（PayPaythonのlink_receiveメソッドを使用）
                try:
                    # パスワードが入力されている場合はパスワード付きで受け取り
                    password = self.password.value.strip() if self.password.value else None
                    
                    if password:
                        receive_result = paypay.link_receive(paypay_url, password)
                    else:
                        receive_result = paypay.link_receive(paypay_url)
                    
                    payment_confirmed = True
                    payment_message = "✅ 支払いが確認されました"
                except Exception as receive_error:
                    payment_confirmed = False
                    payment_message = "❌ 支払いの受け取りに失敗しました"
                    await interaction.response.send_message(f"❌ 支払いの受け取りに失敗しました: {receive_error}", ephemeral=True)
                    return
                
            except Exception as paypay_error:
                await interaction.response.send_message(f"❌ PayPayリンクの処理に失敗しました: {paypay_error}", ephemeral=True)
                return
            
            # 商品情報を取得
            all_stock = load_all_stock()
            target_product = None
            for product in all_stock["products"]:
                if product["id"] == purchase_info["product_id"]:
                    target_product = product
                    break
            
            if not target_product:
                await interaction.response.send_message("❌ 商品情報が見つかりません。", ephemeral=True)
                return
            
            # 商品データファイルを読み込み
            product_data_file = f'stock/{purchase_info["product_id"]}.json'
            try:
                with open(product_data_file, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
            except FileNotFoundError:
                await interaction.response.send_message("❌ 商品データファイルが見つかりません。", ephemeral=True)
                return
            
            if not product_data.get("data") or len(product_data["data"]) == 0:
                await interaction.response.send_message("❌ 商品データがありません。", ephemeral=True)
                return
            
            # 購入者にDMを送信
            try:
                user = interaction.user
                
                # 商品データを送信
                embed = discord.Embed(
                    title=f"🎉 購入完了: {target_product['name']}",
                    description="ご購入ありがとうございます！",
                    color=0x00ff00,
                    timestamp=discord.utils.utcnow()
                )
                
                embed.add_field(name="📦 商品名", value=target_product['name'], inline=True)
                embed.add_field(name="📊 数量", value=f"{purchase_info['quantity']}個", inline=True)
                embed.add_field(name="💵 支払い金額", value=f"¥{purchase_info['total_price']:,}", inline=True)
                
                # 購入数量分の商品データを送信
                data_urls = []
                for i in range(min(purchase_info['quantity'], len(product_data["data"]))):
                    data_urls.append(product_data["data"][i])
                
                if len(data_urls) == 1:
                    embed.add_field(name="📎 商品データ", value=f"[ダウンロード]({data_urls[0]})", inline=False)
                else:
                    data_text = "\n".join([f"{i+1}. [ダウンロード]({url})" for i, url in enumerate(data_urls)])
                    embed.add_field(name="📎 商品データ", value=data_text, inline=False)
                
                embed.set_footer(text="†NEO睡眠† 自販機システム")
                
                await user.send(embed=embed)
                
                # 購入完了ロールを付与
                try:
                    purchase_role = interaction.guild.get_role(1399741605707120683)
                    if purchase_role and purchase_role not in interaction.user.roles:
                        await interaction.user.add_roles(purchase_role)
                except Exception as role_error:
                    print(f"ロール付与エラー: {role_error}")
                
                # 在庫が無限でない場合、購入数量分のデータを削除
                stock_data = load_product_stock(purchase_info["product_id"])
                if stock_data["stock"] != -1:
                    # 在庫を減らす
                    new_stock = stock_data["stock"] - purchase_info["quantity"]
                    
                    # 購入数量分のデータを削除（先頭から削除）
                    for i in range(purchase_info["quantity"]):
                        if len(product_data["data"]) > 0:
                            product_data["data"].pop(0)
                    
                    # 在庫とデータを保存
                    save_product_stock(purchase_info["product_id"], new_stock, product_data["data"])
                
                # 購入完了メッセージを作成
                confirm_embed = discord.Embed(
                    title="🛒 購入完了",
                    description=f"**{target_product['name']}** の購入が完了しました！",
                    color=0x00ff00,
                    timestamp=discord.utils.utcnow()
                )
                
                confirm_embed.add_field(name="📦 商品名", value=target_product['name'], inline=True)
                confirm_embed.add_field(name="📊 数量", value=f"{purchase_info['quantity']}個", inline=True)
                confirm_embed.add_field(name="💰 単価", value=f"¥{target_product['price']:,}", inline=True)
                confirm_embed.add_field(name="💵 合計金額", value=f"¥{purchase_info['total_price']:,}", inline=True)
                confirm_embed.add_field(name="💳 支払い状態", value=payment_message, inline=False)
                confirm_embed.add_field(name="✅ 状態", value="商品データをDMで送信しました！", inline=False)
                
                confirm_embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
                
                await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
                
                # 購入情報ファイルを削除
                os.remove(self.purchase_file)
                
            except Exception as dm_error:
                await interaction.response.send_message(f"❌ DM送信に失敗しました: {dm_error}", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ エラーが発生しました: {e}", ephemeral=True)

@tree.command(name="kwtkzk-auto-setup", description="自販機自動配置設定を追加")
@app_commands.describe(
    channel_id="チャンネルID",
    machine_id="自販機ID"
)
async def kwtkzk_auto_setup(interaction: discord.Interaction, channel_id: str, machine_id: str):
    # 管理者権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('❌ このコマンドは管理者のみ使用できます。', ephemeral=True)
        return
    
    try:
        # チャンネルの存在確認
        channel = client.get_channel(int(channel_id))
        if not channel:
            await interaction.response.send_message(f'❌ チャンネルID `{channel_id}` が見つかりません。', ephemeral=True)
            return
        
        # 自販機の存在確認
        vending_machines = load_vending_machines()
        machine_exists = False
        for machine in vending_machines.get("machines", []):
            if machine.get("id") == machine_id:
                machine_exists = True
                machine_name = machine.get("name", machine_id)
                break
        
        if not machine_exists:
            await interaction.response.send_message(f'❌ 自販機ID `{machine_id}` が見つかりません。', ephemeral=True)
            return
        
        # 既存の設定を読み込み
        auto_config = load_auto_vending_config()
        
        # 重複チェック
        for config in auto_config:
            if config.get("id") == machine_id:
                await interaction.response.send_message(f'❌ 自販機ID `{machine_id}` は既に設定されています。', ephemeral=True)
                return
            if config.get("channel") == channel_id:
                await interaction.response.send_message(f'❌ チャンネルID `{channel_id}` は既に設定されています。', ephemeral=True)
                return
        
        # 新しい設定を追加
        new_config = {
            "id": machine_id,
            "channel": channel_id
        }
        auto_config.append(new_config)
        
        # 設定を保存
        save_auto_vending_config(auto_config)
        
        embed = discord.Embed(
            title="✅ 自販機自動配置設定を追加しました",
            description=f"自販機 `{machine_name}` をチャンネル <#{channel_id}> に自動配置するように設定しました。",
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="🏪 自販機", value=machine_name, inline=True)
        embed.add_field(name="📺 チャンネル", value=f"<#{channel_id}>", inline=True)
        embed.add_field(name="🆔 自販機ID", value=machine_id, inline=True)
        embed.add_field(name="📝 設定ファイル", value="`stock/auto_vending_config.json`", inline=False)
        
        embed.set_footer(text="†NEO睡眠† 自販機システム", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message(embed=embed)
        
    except ValueError:
        await interaction.response.send_message('❌ チャンネルIDは数字で入力してください。', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'❌ エラーが発生しました: {e}', ephemeral=True)

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
