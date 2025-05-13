def send_cart_update_email(user_email, action_type, product_name=None):
    try:
        subject = 'Sepet Güncellemesi'
        if action_type == 'add':
            body = f'"{product_name}" ürünü sepetinize eklendi. Alışverişinizi tamamlamak için sitemizi ziyaret edebilirsiniz.'
        elif action_type == 'remove':
            body = f'"{product_name}" ürünü sepetinizden çıkarıldı.'
        elif action_type == 'update':
            body = f'Sepetinizdeki bir ürün güncellendi.'
        else:
            body = 'Sepetiniz güncellendi.'
        print(f"E-posta gönderildi: {user_email}, {subject}, {body}")
        return True
    except Exception as e:
        print(f"E-posta gönderme hatası: {str(e)}")
        return False 