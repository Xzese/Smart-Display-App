#!/usr/bin/env python3
import os
import requests
import dotenv
import datetime
import tkinter as tk
from PIL import Image, ImageTk

os.chdir(os.path.dirname(os.path.abspath(__file__)))

dotenv.load_dotenv()

# If you already have the access token, you can use it directly

def exchange_facebook_token_for_instagram(facebook_access_token):

    endpoint_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'fb_exchange_token': facebook_access_token
    }
    request_date = datetime.datetime.now()
    response = requests.get(endpoint_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        try:
            # Parse the JSON response
            instagram_access_token = response.json()['access_token']
            expiry_date = request_date + datetime.timedelta(seconds=response.json()['expires_in'])
            os.environ['LONG_ACCESS_TOKEN'] = instagram_access_token
            os.environ['LONG_ACCESS_TOKEN_EXPIRY'] = str(expiry_date)
            dotenv.set_key('.env',"LONG_ACCESS_TOKEN", instagram_access_token)
            dotenv.set_key('.env',"LONG_ACCESS_TOKEN_EXPIRY", str(expiry_date))
            return "Token Exchange Success"
        except:
            os.environ['SHORT_ACCESS_TOKEN'] = ''
            dotenv.set_key('.env',"SHORT_ACCESS_TOKEN", '')
            return None
    else:
        # Handle the error
        print("Error Exchange Token:", response.text)
        return None
    
def refresh_token(unexpired_ig_token):

    endpoint_url = 'https://graph.instagram.com/refresh_access_token'
    params = {
        'grant_type': 'ig_refresh_token',
        'access_token': unexpired_ig_token
    }

    request_date = datetime.datetime.now()
    response = requests.get(endpoint_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        try:
            # Parse the JSON response
            instagram_access_token = response.json()['access_token']
            expiry_date = request_date + datetime.timedelta(seconds=response.json()['expires_in'])
            os.environ['LONG_ACCESS_TOKEN'] = instagram_access_token
            os.environ['LONG_ACCESS_TOKEN_EXPIRY'] = str(expiry_date)
            dotenv.set_key('.env',"LONG_ACCESS_TOKEN", instagram_access_token)
            dotenv.set_key('.env',"LONG_ACCESS_TOKEN_EXPIRY", str(expiry_date))
            return "Token Refresh Success"
        except:
            os.environ['LONG_ACCESS_TOKEN'] = ''
            os.environ['LONG_ACCESS_TOKEN_EXPIRY'] = ''
            dotenv.set_key('.env',"LONG_ACCESS_TOKEN", '')
            dotenv.set_key('.env',"LONG_ACCESS_TOKEN_EXPIRY", '')
            return None
    else:
        # Handle the error
        print(" Error Refresh Token:", response.text)
        print(" Error Refresh Token:" + str(response.raw()))
        return None

def update_ig_stats(): 

    access_token = get_token()
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

def get_token():
    while True:
        if (len(os.getenv('LONG_ACCESS_TOKEN_EXPIRY')) == 0 or len(os.getenv('LONG_ACCESS_TOKEN')) == 0) and len(os.getenv('SHORT_ACCESS_TOKEN')) == 0:
            SHORT_ACCESS_TOKEN = input('Please Retrieve FB Access token from https://developers.facebook.com/tools/explorer/ and paste here: ')
            os.environ['SHORT_ACCESS_TOKEN'] = SHORT_ACCESS_TOKEN
            dotenv.set_key('.env',"SHORT_ACCESS_TOKEN", SHORT_ACCESS_TOKEN)
        elif (len(os.getenv('LONG_ACCESS_TOKEN_EXPIRY')) == 0 or len(os.getenv('LONG_ACCESS_TOKEN')) == 0) and len(os.getenv('SHORT_ACCESS_TOKEN')) != 0:
            instagram_access_token_result = exchange_facebook_token_for_instagram(os.environ['SHORT_ACCESS_TOKEN'])
            print(instagram_access_token_result)
        elif datetime.datetime.strptime(os.getenv('LONG_ACCESS_TOKEN_EXPIRY'), '%Y-%m-%d %H:%M:%S.%f') < datetime.datetime.now():
            print('IG Token Expired')
            os.environ['LONG_ACCESS_TOKEN'] = ''
            os.environ['LONG_ACCESS_TOKEN_EXPIRY'] = ''
            dotenv.set_key('.env',"LONG_ACCESS_TOKEN", '')
            dotenv.set_key('.env',"LONG_ACCESS_TOKEN_EXPIRY", '')
        #elif (datetime.datetime.strptime(os.getenv('LONG_ACCESS_TOKEN_EXPIRY'), '%Y-%m-%d %H:%M:%S.%f') - datetime.datetime.now()).days < 59:
        #    instagram_access_token_result = refresh_token(os.environ['LONG_ACCESS_TOKEN'])
        #    print(instagram_access_token_result)
        
        else:
            return os.environ['LONG_ACCESS_TOKEN']

def get_weather():
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
        current_hour = datetime.datetime.now().hour
        forecast_hour = 12 if current_hour < 12 else 18 if current_hour < 18 else 36
        time_name = "Afternoon" if forecast_hour == 12 else "Evening" if forecast_hour == 18 else "Tomorrow"
        if forecast_hour >= 24:
            return time_name, weather_data['forecast']['forecastday'][1]['hour'][forecast_hour - 24]
        else:
            return time_name, weather_data['forecast']['forecastday'][0]['hour'][forecast_hour]
    else:
        # Print the error message if the request was not successful
        print("Error Update User ID:", response.text)
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
        resized_image = image.resize((int(image_width * scale_factor), int(image_height * scale_factor)), Image.BILINEAR)
        
        # Convert the resized image to a Tkinter PhotoImage
        photo_image = ImageTk.PhotoImage(resized_image)
        
        return photo_image
    except Exception as e:
        print("Error:", e)
        return None
    
if os.getenv('PAGE_TRANSITION_TIME') is None:
    os.environ['PAGE_TRANSITION_TIME'] = '10'
    dotenv.set_key('.env',"PAGE_TRANSITION_TIME", os.environ["PAGE_TRANSITION_TIME"])
if os.getenv('FULLSCREEN') is None:
    os.environ['FULLSCREEN'] = 'true'
    dotenv.set_key('.env',"FULLSCREEN", os.environ["FULLSCREEN"])
if os.getenv('CAROUSEL') is None:
    os.environ['CAROUSEL'] = 'true'
    dotenv.set_key('.env',"CAROUSEL", os.environ["CAROUSEL"])

page_transition_time = int(os.getenv('PAGE_TRANSITION_TIME'))
screen_refresh_process = None
carousel_update_process = None
current_screen = None

def switch_to_clock():
    global screen_refresh_process, screen_image, current_screen, carousel_update_process, page_transition_time
    current_screen = "Clock"
    root.after_cancel(carousel_update_process) if carousel_update_process else None
    root.after_cancel(screen_refresh_process) if screen_refresh_process else None
    pagelabel.configure(text="Time")
    instagram_value.place_forget()
    time_value.place(x=260+20, y=100, width=920, height=200)
    date_value.place(x=1160, y=100, width=180, height=200)
    weather_value.place_forget()
    screen_image = fit_image_to_widget(os.path.join("images","Clock.png"),250,250)
    screenlogo.configure(image=screen_image)
    refresh_clock()
    carousel_update_process = root.after(1000 * page_transition_time, start_carousel) if os.getenv('CAROUSEL') != "false" else None

def refresh_clock():
    global screen_refresh_process
    try:
        date_value.configure(text=datetime.datetime.now().strftime("%d\n%b"))
        time_value.configure(text=datetime.datetime.now().strftime("%H:%M:%S"),fg="white")
    except Exception as e:
        print("An error occured with update clock page: ", e)
    screen_refresh_process = root.after(500, refresh_clock)

def switch_to_instagram():
    global screen_refresh_process, screen_image, current_screen, carousel_update_process, page_transition_time
    current_screen = "Instagram"
    root.after_cancel(carousel_update_process) if carousel_update_process else None
    root.after_cancel(screen_refresh_process) if screen_refresh_process else None
    pagelabel.configure(text="Followers")
    instagram_value.place(x=280, y=100, width=960, height=200)
    time_value.place_forget()
    date_value.place_forget()
    weather_value.place_forget()
    screen_image = fit_image_to_widget(os.path.join("images","Camera.png"),250,250)
    screenlogo.configure(image=screen_image)
    refresh_instagram()
    carousel_update_process = root.after(1000 * page_transition_time, start_carousel) if os.getenv('CAROUSEL') != "false" else None

def refresh_instagram():
    global screen_refresh_process
    try:
        update_ig_stats()
        instagram_value.configure(text="{:,}".format(int(os.getenv('IG_FOLLOWERS_COUNT'))))
        change = os.getenv('IG_FOLLOWER_CHANGE')
        if change == "Increase":
            # Alternate color every second between white and green
            if instagram_value.cget('fg') == 'white':
                instagram_value.configure(fg='#32CD32')
            else:
                instagram_value.configure(fg='white')
        elif change == "Decrease":
            # Alternate color every second between white and red
            if instagram_value.cget('fg') == 'white':
                instagram_value.configure(fg='#FF6347')
            else:
                instagram_value.configure(fg='white')
        else:
            # Reset to default color (white) if the environment variable is not set to "Increase" or "Decrease"
            instagram_value.configure(fg='white')
    except Exception as e:
        print("An error occured with update instagram page: ", e)
    screen_refresh_process = root.after(1000 * 1, refresh_instagram)

def switch_to_weather():
    global screen_refresh_process, screen_image, current_screen, carousel_update_process, page_transition_time
    current_screen = "Weather"
    root.after_cancel(carousel_update_process) if carousel_update_process else None
    root.after_cancel(screen_refresh_process) if screen_refresh_process else None
    instagram_value.place_forget()
    time_value.place_forget()
    date_value.place_forget()
    weather_value.place(x=280, y=100, width=960, height=200)
    screen_image = fit_image_to_widget(os.path.join("images","Weather.png"),250,250)
    screenlogo.configure(image=screen_image)
    refresh_weather()
    carousel_update_process = root.after(1000 * page_transition_time, start_carousel) if os.getenv('CAROUSEL') != "false" else None

def refresh_weather():
    global screen_refresh_process
    try:
        time_name, weather = get_weather()
        print(weather)
        pagelabel.configure(text="Weather Forecast - " + time_name)
        weather_value.configure(text=(str(weather['temp_c'])+'°C, '+weather['condition']['text']))
    except Exception as e:
        print("An error occured with update weather page: ", e)
    screen_refresh_process = root.after(1000*30, refresh_weather)

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
    
# Create the main window
root = tk.Tk()

display_width = 1480
display_height = 320
root.geometry(str(display_width) + 'x' + str(display_height))
root.title("Smart Display")

root.attributes('-fullscreen', False if os.getenv('FULLSCREEN') == "false" else True)

root.configure(bg="black", cursor="none")

text_font = 'Arial Rounded MT Bold'

screenlogo = tk.Label(root, bg="black", fg="white")
screenlogo.place(x=10, y=(display_height-250)/2, width=250, height=250)

pagelabel = tk.Label(root, bg="black", fg="white", font=(text_font, 50), anchor="center")
pagelabel.place(x=280, y=10, width=960, height=100)

time_value = tk.Label(root, bg="black", fg="white", font=(text_font, 150), anchor="center")
date_value = tk.Label(root, bg="black", fg="white", font=(text_font, 50), anchor="center")
instagram_value = tk.Label(root, bg="black", fg="white", font=(text_font, 125), anchor="center")
weather_value = tk.Label(root, bg="black", fg="white", font=(text_font, 60), anchor="center")

clockimage = fit_image_to_widget(os.path.join("images","Clock.png"),50,50)
clockbutton = tk.Button(root, image=clockimage, bg="black", width=50, height=50, command=switch_to_clock, bd=0, highlightthickness=0)
clockbutton.place(x=display_width-50-10,y=30,width=50,height=50)

cameraimage = fit_image_to_widget(os.path.join("images","Camera.png"),50,50)
instagrambutton = tk.Button(root, image=cameraimage, bg="black", width=50, height=50, command=switch_to_instagram, bd=0, highlightthickness=0)
instagrambutton.place(x=display_width-50-10,y=(display_height-50)/2,width=50,height=50)

weatherimage = fit_image_to_widget(os.path.join("images","Weather.png"),50,50)
weatherbutton = tk.Button(root, image=weatherimage, bg="black", fg="black", width=50, height=50, command=switch_to_weather, bd=0, highlightthickness=0)
weatherbutton.place(x=display_width-50-10,y=display_height-50-30,width=50,height=50)

start_carousel()

# Run the Tkinter event loop
root.mainloop()