from PayPaython_mobile import PayPay
import time

def login_with_url():
    try:
        #電話番号とパスワード入力
        phone_number = input("PayPayに登録中の電話番号を入力してください: ").strip()
        password = input("パスワードを入力してください: ").strip()

        # PayPayインスタンスを作成
        paypay = PayPay(phone_number, password, proxy=None)
        
        # URLを入力
        paypay_url = input("PayPay URLを入力してください: ").strip()
        
        if not paypay_url:
            print("❌ URLが入力されていません。")
            return None
        
        # URLの形式チェック
        if not paypay_url.startswith("https://www.paypay.ne.jp/portal/oauth2/"):
            print("❌ 無効なPayPay URL形式です。")
            print("   正しい形式: https://www.paypay.ne.jp/portal/oauth2/l?id=...")
            return None
        
        # URLでログイン
        try:
            print("URL認証を実行中...")
            paypay.login(paypay_url)
            print("✅ URL認証に成功しました！")
            
            return paypay
            
        except Exception as url_error:
            error_str = str(url_error)
            print(f"❌ URL認証に失敗しました: {url_error}")
            
            # エラーの詳細分析
            if "OTL_NOT_FOUND" in error_str or "Code not found" in error_str:
                print("\n🔍 エラー分析:")
                print("   • URLが期限切れまたは無効です")
                print("   • PayPayアプリで新しい認証URLを生成してください")
                print("   • 生成後すぐに使用してください")
            elif "Bad credentials" in error_str:
                print("\n🔍 エラー分析:")
                print("   • 認証情報が間違っています")
                print("   • 電話番号とパスワードを確認してください")
            elif "OTP" in error_str:
                print("\n🔍 エラー分析:")
                print("   • OTP認証が必要です")
                print("   • OTP認証方法を選択してください")
            
            return None
            
    except Exception as e:
        print(f"❌ URL認証エラー: {e}")
        return None

def main():
    print("PayPayトークン取得ツール")
    print("=" * 30)
    paypay = login_with_url()
    
    if 'paypay' in locals() and paypay:
        print("取得したトークン情報:")
        print(f"リフレッシュトークン: {paypay.refresh_token}")
        print("\nこれらのトークンをmain.pyで使用してください。")

if __name__ == "__main__":
    main()