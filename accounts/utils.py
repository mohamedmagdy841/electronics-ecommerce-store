# import os
# from twilio.rest import Client

def send_otp_via_sms(phone_number, otp):
    print(f"Sending OTP {otp} to {phone_number}")
    # client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    # client.messages.create(
    #     body=f"Your OTP is {otp}",
    #     from_=os.getenv("TWILIO_PHONE_NUMBER"),
    #     to=phone_number
    # )
