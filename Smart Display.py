#!/usr/bin/env python3
import os
import requests
import dotenv
import datetime
import tkinter as tk
import qrcode
import threading
from auth_server import wait_for_token, get_auth_url, native_capture
from PIL import Image, ImageTk

os.chdir(os.path.dirname(os.path.abspath(__file__)))

dotenv.load_dotenv()

def update_ig_stats(): 

    access_token = os.getenv('LONG_ACCESS_TOKEN')
    user_id = os.getenv('IG_BUSINESS_USER_ID')

    #get Business Account ID if missing
    if len(user_id) == 0:
        endpoint_url = 'https://graph.facebook.com/v19.0/me/accounts'
        params = {
            'fields': 'instagram_business_account{id,username}',
            'access_token': access_token
        }
        response = requests.get(endpoint_url, params=params)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            ig_business_account = response.json()
            os.environ['IG_BUSINESS_USER_ID'] = ig_business_account['data'][0]['instagram_business_account']['id']
            dotenv.set_key('.env',"IG_BUSINESS_USER_ID", os.environ["IG_BUSINESS_USER_ID"])
            user_id = os.getenv('IG_BUSINESS_USER_ID')
            print('Retrived Business Account ID: ' + os.getenv('IG_BUSINESS_USER_ID'))
        else:
            # Print the error message if the request was not successful
            print("Error Update User ID:", response.text)
            return None

    update_required = True

    if len(os.getenv('IG_LAST_UPDATED')) == 0:
        update_required = True
    elif (datetime.datetime.now() - datetime.datetime.strptime(os.getenv('IG_LAST_UPDATED'), '%Y-%m-%d %H:%M:%S.%f')). total_seconds() > 20:
        update_required = True
    else:
        update_required = False

    if update_required:
        endpoint_url = 'https://graph.facebook.com/v19.0/' + user_id
        params = {
            'fields': 'id,username,followers_count,follows_count,media_count',
            'access_token': access_token
        }
        # Send a GET request to the endpoint URL with the parameters
        response = requests.get(endpoint_url, params=params)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            account_details = response.json()
            # Print the user's profile information
            os.environ['IG_FOLLOWER_CHANGE'] = "None" if int(account_details['followers_count']) == int(os.environ['IG_FOLLOWERS_COUNT']) else "Increase" if int(account_details['followers_count']) > int(os.environ['IG_FOLLOWERS_COUNT']) else "Decrease"
            os.environ['IG_FOLLOWERS_COUNT'] = str(account_details['followers_count'])
            os.environ['IG_FOLLOWS_COUNT'] = str(account_details['follows_count'])
            os.environ['IG_LAST_UPDATED'] = str(datetime.datetime.now())
            dotenv.set_key('.env',"IG_FOLLOWER_CHANGE", os.environ["IG_FOLLOWER_CHANGE"])
            dotenv.set_key('.env',"IG_FOLLOWERS_COUNT", os.environ["IG_FOLLOWERS_COUNT"])
            dotenv.set_key('.env',"IG_FOLLOWS_COUNT", os.environ["IG_FOLLOWS_COUNT"])
            dotenv.set_key('.env',"IG_LAST_UPDATED", os.environ["IG_LAST_UPDATED"])
            print("Followers: " + os.environ['IG_FOLLOWERS_COUNT'] + "\nFollowing: " + os.environ['IG_FOLLOWS_COUNT'])
        else:
            # Print the error message if the request was not successful
            print("Error Update IG Stats:", response.text)
            return None

    return "IG Stats Updated Successfully"

def get_weather():
    if os.getenv('WEATHER_LAST_UPDATED') is None or (datetime.datetime.now() - datetime.datetime.strptime(os.getenv('WEATHER_LAST_UPDATED'), '%Y-%m-%d %H:%M:%S.%f')). total_seconds() > 60:
        endpoint_url = 'https://api.weatherapi.com/v1/forecast.json'
        params = {
            'key': os.getenv('WEATHER_API_KEY'),
            'q': os.getenv('WEATHER_LOCATION'),
            'days': '2',
            'aqi': 'no',
            'alerts': 'no',
        }
        response = requests.get(endpoint_url, params=params)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            weather_data = response.json()

            current_time = datetime.datetime.now()
            forecast_hour = 12 if current_time.hour < 10 else 18 if current_time.hour < 16 else 36
            forecast_weather = weather_data['forecast']['forecastday'][1]['hour'][forecast_hour - 24] if forecast_hour >= 24 else weather_data['forecast']['forecastday'][0]['hour'][forecast_hour]

            os.environ['WEATHER_LAST_UPDATED'] = str(current_time)
            os.environ['WEATHER_NOW_TEMP'] = str(weather_data['current']['temp_c'])
            os.environ['WEATHER_NOW_CONDITIONS'] = str(weather_data['current']['condition']['text'])
            os.environ['WEATHER_FUTURE_TIME'] = "Afternoon" if forecast_hour == 12 else "Evening" if forecast_hour == 18 else "Tomorrow"
            os.environ['WEATHER_FUTURE_TEMP'] = str(forecast_weather['temp_c'])
            os.environ['WEATHER_FUTURE_CONDITIONS'] = str(forecast_weather['condition']['text'])
            dotenv.set_key('.env',"WEATHER_LAST_UPDATED", os.environ['WEATHER_LAST_UPDATED'])
            dotenv.set_key('.env',"WEATHER_NOW_TEMP", os.environ['WEATHER_NOW_TEMP'])
            dotenv.set_key('.env',"WEATHER_NOW_CONDITIONS", os.environ['WEATHER_NOW_CONDITIONS'])
            dotenv.set_key('.env',"WEATHER_FUTURE_TIME", os.environ['WEATHER_FUTURE_TIME'])
            dotenv.set_key('.env',"WEATHER_FUTURE_TEMP", os.environ['WEATHER_FUTURE_TEMP'])
            dotenv.set_key('.env',"WEATHER_FUTURE_CONDITIONS", os.environ['WEATHER_FUTURE_CONDITIONS'])
        else:
            # Print the error message if the request was not successful
            print("Error Get Weather:", response.text)
            return None

def fit_image_to_widget(image_path, widget_width, widget_height):
    try:
        # Open the image using PIL (Python Imaging Library)
        image = Image.open(image_path)
        
        # Get the width and height of the image
        image_width, image_height = image.size
        
        # Calculate the scale factor for width and height
        width_scale = widget_width / image_width
        height_scale = widget_height / image_height
        
        # Choose the smaller scale factor to ensure the image fits within the widget
        scale_factor = min(width_scale, height_scale)
        
        # Resize the image using the calculated scale factor
        resized_image = image.resize((int(image_width * scale_factor), int(image_height * scale_factor)), Image.BICUBIC)
        
        # Convert the resized image to a Tkinter PhotoImage
        photo_image = ImageTk.PhotoImage(resized_image)
        
        return photo_image
    except Exception as e:
        print("Error:", e)
        return None
    
def initialize_environment():
    if os.getenv('PAGE_TRANSITION_TIME') is None:
        os.environ['PAGE_TRANSITION_TIME'] = '10'
        dotenv.set_key('.env',"PAGE_TRANSITION_TIME", os.environ["PAGE_TRANSITION_TIME"])
    if os.getenv('FULLSCREEN') is None:
        os.environ['FULLSCREEN'] = 'true'
        dotenv.set_key('.env',"FULLSCREEN", os.environ["FULLSCREEN"])
    if os.getenv('CAROUSEL') is None:
        os.environ['CAROUSEL'] = 'true'
        dotenv.set_key('.env',"CAROUSEL", os.environ["CAROUSEL"])
    return int(os.getenv('PAGE_TRANSITION_TIME')), None, None, None

def switch_to_clock():
    global screen_refresh_process, current_screen, carousel_update_process, page_transition_time
    current_screen = "Clock"
    root.after_cancel(carousel_update_process) if carousel_update_process else None
    root.after_cancel(screen_refresh_process) if screen_refresh_process else None
    clear_page_transition()
    clock_logo.place(x=10, y=(display_height-250)/2, width=250, height=250)
    clock_label.place(x=260, y=10, width=1000, height=100)
    clock_time.place(x=260+20, y=100, width=920, height=200)
    clock_date.place(x=1160, y=100, width=180, height=200)
    refresh_clock()
    carousel_update_process = root.after(1000 * page_transition_time, start_carousel) if os.getenv('CAROUSEL') != "false" else None

def refresh_clock():
    global screen_refresh_process
    try:
        clock_date.configure(text=datetime.datetime.now().strftime("%d\n%b"))
        clock_time.configure(text=datetime.datetime.now().strftime("%H:%M:%S"),fg="white")
    except Exception as e:
        print("An error occured with update clock page: ", e)
    screen_refresh_process = root.after(500, refresh_clock)

def switch_to_instagram():
    global screen_refresh_process, current_screen, carousel_update_process, page_transition_time
    current_screen = "Instagram"
    root.after_cancel(carousel_update_process) if carousel_update_process else None
    root.after_cancel(screen_refresh_process) if screen_refresh_process else None
    clear_page_transition()
    camera_logo.place(x=10, y=(display_height-250)/2, width=250, height=250)
    instagram_label.place(x=260, y=10, width=1000, height=100)
    instagram_followers.place(x=280, y=100, width=960, height=200)
    refresh_instagram()
    carousel_update_process = root.after(1000 * page_transition_time, start_carousel) if os.getenv('CAROUSEL') != "false" else None

def refresh_instagram():
    global screen_refresh_process
    try:
        update_ig_stats()
        instagram_followers.configure(text="{:,}".format(int(os.getenv('IG_FOLLOWERS_COUNT'))))
        change = os.getenv('IG_FOLLOWER_CHANGE')
        if change == "Increase":
            # Alternate color every second between white and green
            if instagram_followers.cget('fg') == 'white':
                instagram_followers.configure(fg='#32CD32')
            else:
                instagram_followers.configure(fg='white')
        elif change == "Decrease":
            # Alternate color every second between white and red
            if instagram_followers.cget('fg') == 'white':
                instagram_followers.configure(fg='#FF6347')
            else:
                instagram_followers.configure(fg='white')
        else:
            # Reset to default color (white) if the environment variable is not set to "Increase" or "Decrease"
            instagram_followers.configure(fg='white')
    except Exception as e:
        print("An error occured with update instagram page: ", e)
    screen_refresh_process = root.after(1000 * 1, refresh_instagram)

def switch_to_weather():
    global screen_refresh_process, current_screen, carousel_update_process, page_transition_time
    current_screen = "Weather"
    root.after_cancel(carousel_update_process) if carousel_update_process else None
    root.after_cancel(screen_refresh_process) if screen_refresh_process else None
    clear_page_transition()
    weather_now_label.place(x=260, y=100, width=480, height=40)
    weather_now_temp.place(x=260, y=155, width=480, height=80)
    weather_now_conditions.place(x=260, y=235, width=480, height=80)
    weather_future_label.place(x=760, y=100, width=480, height=40)
    weather_future_temp.place(x=760, y=155, width=480, height=80)
    weather_future_conditions.place(x=760, y=235, width=480, height=80)
    weather_logo.place(x=10, y=(display_height-250)/2, width=250, height=250)
    weather_label.place(x=260, y=10, width=1000, height=100)
    refresh_weather()
    carousel_update_process = root.after(1000 * page_transition_time, start_carousel) if os.getenv('CAROUSEL') != "false" else None

def refresh_weather():
    global screen_refresh_process
    try:
        get_weather()
        weather_now_temp.configure(text=str(os.getenv('WEATHER_NOW_TEMP'))+"°C")
        weather_now_conditions.configure(text=str(os.getenv('WEATHER_NOW_CONDITIONS')))
        weather_future_temp.configure(text=str(os.getenv('WEATHER_FUTURE_TEMP'))+"°C")
        weather_future_conditions.configure(text=str(os.getenv('WEATHER_FUTURE_CONDITIONS')))
        weather_future_label.configure(text=str(os.getenv('WEATHER_FUTURE_TIME')))
    except Exception as e:
        print("An error occured with update weather page: ", e)
    screen_refresh_process = root.after(1000*1, refresh_weather)

def switch_to_settings():
    global screen_refresh_process, current_screen, carousel_update_process
    current_screen = "Settings"
    root.after_cancel(carousel_update_process) if carousel_update_process else None
    root.after_cancel(screen_refresh_process) if screen_refresh_process else None
    clear_page_transition()
    root.configure(bg="#505050")
    settings_button.configure(bg="#505050")
    clock_button.configure(bg="#505050")
    instagram_button.configure(bg="#505050")
    weather_button.configure(bg="#505050")
    settings_logo.place(x=10, y=(display_height-250)/2, width=250, height=250)
    settings_label.place(x=260, y=10, width=1000, height=100)
    token_days_remaining = (datetime.datetime.strptime(os.getenv('LONG_ACCESS_TOKEN_EXPIRY'), '%Y-%m-%d %H:%M:%S.%f') - datetime.datetime.now()).days
    if token_days_remaining >= 0:
        token_label.configure(text="Token Has\n"+str(token_days_remaining)+" Days Remaining")
    else:
        token_label.configure(text="Token Has\n Expired", bg="black")
    token_label.place(x=300, y=110, width=300, height=100)
    refresh_token_button.place(x=350, y=210, width=200, height=50)

def start_carousel():
    global current_screen
    try:
        if current_screen == "Weather":
            switch_to_instagram()
        elif current_screen == None or current_screen == "Instagram":
            switch_to_clock()
        elif current_screen == "Clock":
            switch_to_weather()
    except Exception as e:
        print("An error occured with carousel: ", e)

def clear_page_transition():
    instagram_followers.place_forget()
    clock_time.place_forget()
    clock_date.place_forget()
    weather_now_temp.place_forget()
    weather_now_conditions.place_forget()
    weather_future_temp.place_forget()
    weather_future_conditions.place_forget()
    weather_now_label.place_forget()
    weather_future_label.place_forget()
    clock_logo.place_forget() 
    weather_logo.place_forget()
    camera_logo.place_forget()
    clock_label.place_forget()
    weather_label.place_forget()
    instagram_label.place_forget()
    token_label.place_forget()
    refresh_token_button.place_forget()
    qrcode_image_label.place_forget()
    root.configure(bg="black")
    settings_button.configure(bg="black")
    clock_button.configure(bg="black")
    instagram_button.configure(bg="black")
    weather_button.configure(bg="black")
    refresh_token_button.configure(text="Refresh Token", command=refresh_token)

def check_thread_status(thread):
    if thread.is_alive():
        print("Waiting for Token")
        root.after(1000, check_thread_status, thread)
    else:
        thread.join()
        switch_to_clock()

def refresh_token():
    auth_url = get_auth_url()
    qrcode_image = create_qrcode(auth_url)
    refresh_token_button.configure(command=lambda: native_capture(auth_url), text="Open Browser")
    qrcode_image_label.configure(image=qrcode_image)
    qrcode_image_label.image = qrcode_image
    qrcode_image_label.place(x=600, y=85, width=250, height=250)

    token_thread = threading.Thread(target=wait_for_token)
    token_thread.start()

    root.after(1000, check_thread_status, token_thread)
    
def create_qrcode(auth_url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3.5,
        border=1,
    )
    qr.add_data(auth_url)
    qr.make(fit=True)
    pil_image = qr.make_image(fill_color="black", back_color="white")
    photo_image = ImageTk.PhotoImage(pil_image)
    return photo_image

root = tk.Tk()

text_font = 'Arial Rounded MT Bold'
display_width = 1480
display_height = 320

root.geometry(str(display_width) + 'x' + str(display_height))
root.title("Smart Display")
root.attributes('-fullscreen', False if os.getenv('FULLSCREEN') == "false" else True)
root.configure(bg="black", cursor="none")

cog_image_large = fit_image_to_widget(os.path.join("images","Cog.png"),250,250)
cog_image_small = fit_image_to_widget(os.path.join("images","Cog.png"),50,50)
clock_image_large = fit_image_to_widget(os.path.join("images","Clock.png"),250,250)
clock_image_small = fit_image_to_widget(os.path.join("images","Clock.png"),50,50)
weather_image_large = fit_image_to_widget(os.path.join("images","Weather.png"),250,250)
weather_image_small = fit_image_to_widget(os.path.join("images","Weather.png"),50,50)
camera_image_large = fit_image_to_widget(os.path.join("images","Camera.png"),250,250)
camera_image_small = fit_image_to_widget(os.path.join("images","Camera.png"),50,50)

settings_logo = tk.Label(root, bg="#505050", fg="white", image=cog_image_large)
clock_logo = tk.Label(root, bg="black", fg="white", image=clock_image_large)
weather_logo = tk.Label(root, bg="black", fg="white", image=weather_image_large)
camera_logo = tk.Label(root, bg="black", fg="white", image=camera_image_large)
qrcode_image_label = tk.Label(root, bg="#505050", fg="#505050")

settings_label = tk.Label(root, bg="#505050", fg="white", font=(text_font, 50), anchor="center", text="Settings")
token_label = tk.Label(root, bg="#505050", fg="white", font=(text_font, 20), anchor="center", text="Token Has\nX Days Remaining")
clock_label = tk.Label(root, bg="black", fg="white", font=(text_font, 50), anchor="center", text="Time")
weather_label = tk.Label(root, bg="black", fg="white", font=(text_font, 50), anchor="center", text="Weather")
instagram_label = tk.Label(root, bg="black", fg="white", font=(text_font, 50), anchor="center", text="Followers")
clock_time = tk.Label(root, bg="black", fg="white", font=(text_font, 150), anchor="center")
clock_date = tk.Label(root, bg="black", fg="white", font=(text_font, 50), anchor="center")
instagram_followers = tk.Label(root, bg="black", fg="white", font=(text_font, 125), anchor="center")
weather_now_label = tk.Label(root, bg="black", fg="white", font=(text_font, 30), anchor="center", text="Now")
weather_now_temp = tk.Label(root, bg="black", fg="white", font=(text_font, 70), anchor="center")
weather_now_conditions = tk.Label(root, bg="black", fg="white", font=(text_font, 25), anchor="center", wraplength=480)
weather_future_label = tk.Label(root, bg="black", fg="white", font=(text_font, 30), anchor="center")
weather_future_temp = tk.Label(root, bg="black", fg="white", font=(text_font, 70), anchor="center")
weather_future_conditions = tk.Label(root, bg="black", fg="white", font=(text_font, 25), anchor="center", wraplength=480)

vertical_margin_right = 10
button_size = 50
vertical_margin_top = 15
vertical_margin_bottom = 15

total_button_height = button_size * 4
total_vertical_spacing = vertical_margin_top + vertical_margin_bottom
available_vertical_space = display_height - total_button_height - total_vertical_spacing
vertical_spacing = available_vertical_space / (4 - 1)

refresh_token_button = tk.Button(root, text="Refresh Token", bg="#505050", fg="white",activebackground="grey", activeforeground="white", font=(text_font, 20), command=refresh_token, bd=1, highlightthickness=1)
settings_button = tk.Button(root, image=cog_image_small, bg="black", fg="black", activebackground="grey", width=button_size, height=button_size, command=switch_to_settings, bd=0, highlightthickness=0)
clock_button = tk.Button(root, image=clock_image_small, bg="black", fg="black", activebackground="grey", width=button_size, height=button_size, command=switch_to_clock, bd=0, highlightthickness=0)
instagram_button = tk.Button(root, image=camera_image_small, bg="black", fg="black", activebackground="grey", width=button_size, height=button_size, command=switch_to_instagram, bd=0, highlightthickness=0)
weather_button = tk.Button(root, image=weather_image_small, bg="black", fg="black", activebackground="grey", width=button_size, height=button_size, command=switch_to_weather, bd=0, highlightthickness=0)

settings_button.place(x=display_width-button_size-vertical_margin_right,y=(button_size + vertical_spacing) * 0 + vertical_margin_top,width=button_size,height=button_size)
clock_button.place(x=display_width-button_size-vertical_margin_right,y=(button_size + vertical_spacing) * 1 + vertical_margin_top,width=button_size,height=button_size)
instagram_button.place(x=display_width-button_size-vertical_margin_right,y=(button_size + vertical_spacing) * 2 + vertical_margin_top,width=button_size,height=button_size)
weather_button.place(x=display_width-button_size-vertical_margin_right,y=(button_size + vertical_spacing) * 3 + vertical_margin_top,width=button_size,height=button_size)

page_transition_time, screen_refresh_process, carousel_update_process, current_screen = initialize_environment()

start_carousel()

root.mainloop()