#!/usr/bin/env python3
import os
import requests
import dotenv
import datetime
import tkinter as tk
import qrcode
import threading
import socket
from auth_server import wait_for_token, get_auth_url, local_browser_capture, stop_server
from PIL import Image, ImageTk

os.chdir(os.path.dirname(os.path.abspath(__file__)))

dotenv.load_dotenv()

os.environ['GRAPH_SCOPE'] = "pages_show_list,business_management,instagram_basic"
dotenv.set_key('.env',"GRAPH_SCOPE", os.environ["GRAPH_SCOPE"])

def update_ig_stats():
    if os.getenv('ACCESS_TOKEN') is not None and os.getenv('ACCESS_TOKEN') != '' and os.getenv('ACCESS_TOKEN_EXPIRY') is not None and os.getenv('ACCESS_TOKEN_EXPIRY') != '' and datetime.datetime.strptime(os.getenv('ACCESS_TOKEN_EXPIRY'), '%Y-%m-%d %H:%M:%S.%f') > datetime.datetime.now():
        #get Business Account ID if missing
        if len(os.getenv('IG_BUSINESS_USER_ID')) == 0:
            endpoint_url = 'https://graph.facebook.com/v19.0/me/accounts'
            params = {
                'fields': 'instagram_business_account{id,username}',
                'access_token': os.getenv('ACCESS_TOKEN')
            }
            response = requests.get(endpoint_url, params=params)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the JSON response
                ig_business_account = response.json()
                os.environ['IG_BUSINESS_USER_ID'] = ig_business_account['data'][0]['instagram_business_account']['id']
                dotenv.set_key('.env',"IG_BUSINESS_USER_ID", os.environ["IG_BUSINESS_USER_ID"])
            else:
                # Print the error message if the request was not successful
                print("Error Update User ID:", response.text)
                return None

        update_required = True

        if os.getenv('IG_LAST_UPDATED') is None:
            update_required = True
        elif os.getenv('IG_LAST_UPDATED') == '':
            update_required = True
        elif (datetime.datetime.now() - datetime.datetime.strptime(os.getenv('IG_LAST_UPDATED'), '%Y-%m-%d %H:%M:%S.%f')). total_seconds() > 20:
            update_required = True
        else:
            update_required = False

        if update_required:
            endpoint_url = 'https://graph.facebook.com/v19.0/' + os.getenv('IG_BUSINESS_USER_ID')
            params = {
                'fields': 'id,username,followers_count,follows_count,media_count',
                'access_token': os.getenv('ACCESS_TOKEN')
            }
            # Send a GET request to the endpoint URL with the parameters
            response = requests.get(endpoint_url, params=params)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the JSON response
                account_details = response.json()
                # Print the user's profile information
                try:
                    os.environ['IG_FOLLOWER_CHANGE'] = "None" if int(account_details['followers_count']) == int(os.environ['IG_FOLLOWERS_COUNT']) else "Increase" if int(account_details['followers_count']) > int(os.environ['IG_FOLLOWERS_COUNT']) else "Decrease"
                except:
                    os.environ['IG_FOLLOWER_CHANGE'] = "None"
                os.environ['IG_FOLLOWERS_COUNT'] = str(account_details['followers_count'])
                os.environ['IG_FOLLOWS_COUNT'] = str(account_details['follows_count'])
                os.environ['IG_LAST_UPDATED'] = str(datetime.datetime.now())
                dotenv.set_key('.env',"IG_FOLLOWER_CHANGE", os.environ["IG_FOLLOWER_CHANGE"])
                dotenv.set_key('.env',"IG_FOLLOWERS_COUNT", os.environ["IG_FOLLOWERS_COUNT"])
                dotenv.set_key('.env',"IG_FOLLOWS_COUNT", os.environ["IG_FOLLOWS_COUNT"])
                dotenv.set_key('.env',"IG_LAST_UPDATED", os.environ["IG_LAST_UPDATED"])
            else:
                # Print the error message if the request was not successful
                print("Error Update IG Stats:", response.text)
                return None

        return "IG Stats Updated Successfully"
    else:
        return "No Valid Token"

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
    if os.getenv('PAGE_TRANSITION') is None:
        os.environ['PAGE_TRANSITION'] = 'true'
        dotenv.set_key('.env',"PAGE_TRANSITION", os.environ["PAGE_TRANSITION"])
    if os.getenv('TEXT_FONT') is None:
        os.environ['TEXT_FONT'] = 'Arial Rounded MT Bold'
        dotenv.set_key('.env',"TEXT_FONT", os.environ["TEXT_FONT"])
    if os.getenv('DISPLAY_WIDTH') is None:
        os.environ['DISPLAY_WIDTH'] = '1480'
        dotenv.set_key('.env',"DISPLAY_WIDTH", os.environ["DISPLAY_WIDTH"])
    if os.getenv('DISPLAY_HEIGHT') is None:
        os.environ['DISPLAY_HEIGHT'] = '320'
        dotenv.set_key('.env',"DISPLAY_HEIGHT", os.environ["DISPLAY_HEIGHT"])

def switch_to_clock():
    global clock_refresh_process, current_screen, old_screen
    old_screen = current_screen
    current_screen = "Clock"
    page_transition(old_screen, current_screen, True)
    refresh_clock()
    
def refresh_clock():
    global clock_refresh_process, current_screen, old_screen
    try:
        current_time = datetime.datetime.now()
        clock_date.configure(text=current_time.strftime("%d\n%b"))
        clock_time.configure(text=current_time.strftime("%H:%M:%S"),fg="white")
    except Exception as e:
        print("An error occured with update clock page: ", e)
    root.after_cancel(clock_refresh_process) if clock_refresh_process else None
    if old_screen == "Clock" or current_screen == "Clock":
        clock_refresh_process = root.after(500, refresh_clock)

def switch_to_instagram():
    global instagram_refresh_process, current_screen, old_screen
    old_screen = current_screen
    current_screen = "Instagram"
    page_transition(old_screen, current_screen, True)
    refresh_instagram()

def refresh_instagram():
    global instagram_refresh_process, current_screen
    try:
        ig_stat_update = update_ig_stats()
        if ig_stat_update == "No Valid Token":
            instagram_button.config(state=tk.DISABLED)
            switch_to_clock()
        else:
            instagram_followers.configure(text="{:,}".format(int(os.getenv('IG_FOLLOWERS_COUNT'))), font=(text_font, 125))
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
    root.after_cancel(instagram_refresh_process) if instagram_refresh_process else None
    if current_screen == "Instagram":
        instagram_refresh_process = root.after(1000 * 20, refresh_instagram)

def switch_to_weather():
    global weather_refresh_process, current_screen, old_screen
    old_screen = current_screen
    current_screen = "Weather"
    page_transition(old_screen, current_screen, True)
    refresh_weather()
    
def refresh_weather():
    global weather_refresh_process, current_screen
    try:
        get_weather()
        weather_now_temp.configure(text=str(os.getenv('WEATHER_NOW_TEMP'))+"°C")
        weather_now_conditions.configure(text=str(os.getenv('WEATHER_NOW_CONDITIONS')))
        weather_future_temp.configure(text=str(os.getenv('WEATHER_FUTURE_TEMP'))+"°C")
        weather_future_conditions.configure(text=str(os.getenv('WEATHER_FUTURE_CONDITIONS')))
        weather_future_label.configure(text=str(os.getenv('WEATHER_FUTURE_TIME')))
    except Exception as e:
        print("An error occured with update weather page: ", e)
    root.after_cancel(weather_refresh_process) if weather_refresh_process else None
    if current_screen == "Weather":
        weather_refresh_process = root.after(1000*60, refresh_weather)

def switch_to_settings():
    global current_screen
    old_screen = current_screen
    current_screen = "Settings"
    page_transition(old_screen, current_screen, False)
    root.configure(bg="#505050")
    settings_frame.configure(bg="#505050")
    settings_button.configure(bg="#505050")
    clock_button.configure(bg="#505050")
    instagram_button.configure(bg="#505050")
    weather_button.configure(bg="#505050")
    try:
        ip_address_label.configure(text="Local IP: "+str(get_local_ip()))
    except:
        ip_address_label.configure(text="Local IP is Unavailable")
    token_days_remaining = (datetime.datetime.strptime(os.getenv('ACCESS_TOKEN_EXPIRY'), '%Y-%m-%d %H:%M:%S.%f') - datetime.datetime.now()).days
    if token_days_remaining >= 0:
        token_label.configure(text="Token Has "+str(token_days_remaining)+"\nDays Remaining")
    else:
        token_label.configure(text="Token Has\n Expired")
    carousel_stop_start_label.configure(text="Carousel is Running" if os.getenv('CAROUSEL')=='true' else 'Carousel is Stopped')
    carousel_stop_start_button.configure(text="Stop" if os.getenv('CAROUSEL')=='true' else 'Start')
    page_transition_time_label.configure(text="Page Change Time (s)")
    page_transition_time_var.set(os.getenv("PAGE_TRANSITION_TIME"))

def start_carousel():
    global current_screen
    try:
        if current_screen == "Weather" and instagram_button.cget("state") != tk.DISABLED:
            switch_to_instagram()
        elif current_screen == None or current_screen == "Instagram" or (current_screen == "Weather" and instagram_button.cget("state") == tk.DISABLED):
            switch_to_clock()
        elif current_screen == "Clock":
            switch_to_weather()
    except Exception as e:
        print("An error occured with carousel: ", e)

def carousel_stop_start():
    if os.getenv('CAROUSEL') == 'true':
        os.environ['CAROUSEL'] = 'false'
    else:
        os.environ['CAROUSEL'] = 'true'
    dotenv.set_key('.env',"CAROUSEL", os.environ['CAROUSEL'])
    carousel_stop_start_label.configure(text="Carousel is Running" if os.getenv('CAROUSEL')=='true' else 'Carousel is Stopped')
    carousel_stop_start_button.configure(text="Stop" if os.getenv('CAROUSEL')=='true' else 'Start')

def page_transition_stop_start():
    if os.getenv('PAGE_TRANSITION') == 'true':
        os.environ['PAGE_TRANSITION'] = 'false'
    else:
        os.environ['PAGE_TRANSITION'] = 'true'
    dotenv.set_key('.env',"PAGE_TRANSITION", os.environ['PAGE_TRANSITION'])
    page_transition_start_stop_label.configure(text="Page Transitions are On" if os.getenv('PAGE_TRANSITION')=='true' else 'Page Transitions are Off')
    page_transition_start_stop_button.configure(text="Stop" if os.getenv('PAGE_TRANSITION')=='true' else 'Start')

def page_transition_time():
    os.environ['PAGE_TRANSITION_TIME'] = str(page_transition_time_entry.get())
    dotenv.set_key('.env',"PAGE_TRANSITION_TIME", os.environ['PAGE_TRANSITION_TIME'])
    page_transition_time_var.set(os.getenv("PAGE_TRANSITION_TIME"))

def page_transition_time_decrease():
    if int(page_transition_time_entry.get()) > 1:
        os.environ['PAGE_TRANSITION_TIME'] = str(int(page_transition_time_entry.get()) - 1)
        dotenv.set_key('.env',"PAGE_TRANSITION_TIME", os.environ['PAGE_TRANSITION_TIME'])
        page_transition_time_var.set(os.getenv("PAGE_TRANSITION_TIME"))

def page_transition_time_increase():
    os.environ['PAGE_TRANSITION_TIME'] = str(int(page_transition_time_entry.get()) + 1)
    dotenv.set_key('.env',"PAGE_TRANSITION_TIME", os.environ['PAGE_TRANSITION_TIME'])
    page_transition_time_var.set(os.getenv("PAGE_TRANSITION_TIME"))

def validate_input(text):
    try:
        # Convert the input to an integer
        number = int(text)
        # Check if the number is a digit and greater than 0
        return number > 0
    except ValueError:
        # If conversion to integer fails, input is not a digit
        return False

def page_transition(old_screen, current_screen, transition=False):
    global carousel_update_process, active_transition

    root.after_cancel(active_transition) if active_transition else None
    root.after_cancel(carousel_update_process) if carousel_update_process else None
    if old_screen == current_screen or old_screen == None or old_screen == "Settings" or os.getenv('PAGE_TRANSITION') == 'false':
        transition = False

    if old_screen is not None and old_screen != current_screen:
        pages = list(page_frames.keys())
        if current_screen == "Settings":
            root.after_cancel(clock_refresh_process) if clock_refresh_process else None
            root.after_cancel(instagram_refresh_process) if instagram_refresh_process else None
            root.after_cancel(weather_refresh_process) if weather_refresh_process else None
        elif (old_screen == "Clock" and current_screen == "Instagram") or (old_screen == "Instagram" and current_screen == "Clock"):
            root.after_cancel(weather_refresh_process) if weather_refresh_process else None
        elif (old_screen == "Clock" and current_screen == "Weather") or (old_screen == "Weather" and current_screen == "Clock"):
            root.after_cancel(instagram_refresh_process) if instagram_refresh_process else None
        elif (old_screen != "Clock" and current_screen != "Clock"):
            root.after_cancel(clock_refresh_process) if clock_refresh_process else None
        
        if old_screen in pages: pages.remove(old_screen)
        if current_screen in pages: pages.remove(current_screen)
        for page in pages:
            for item in page_frames[page]:
                item['frame'].place_forget() 

    instagram_button.config(state=tk.NORMAL) if instagram_button.cget("state") != tk.DISABLED else None
    settings_button.config(state=tk.NORMAL)
    clock_button.config(state=tk.NORMAL)
    weather_button.config(state=tk.NORMAL)

    if not transition:
        if old_screen is not None:
            for item in page_frames[old_screen]:
                item['frame'].place_forget()
            if old_screen == "Settings":
                root.configure(bg="black")
                settings_frame.configure(bg="black")
                settings_button.configure(bg="black")
                clock_button.configure(bg="black")
                instagram_button.configure(bg="black")
                weather_button.configure(bg="black")
                refresh_token_button.configure(text="Refresh Token", command=refresh_token)
                qrcode_image_label.place_forget()
                stop_server()
        for item in page_frames[current_screen]:
            item['frame'].place(x=item['x'], y=item['y'], width=item['width'], height=item['height'])
        carousel_update_process = root.after(1000 * int(os.getenv('PAGE_TRANSITION_TIME')), start_carousel) if os.getenv('CAROUSEL') != "false" else None
    elif transition:
        if old_screen == "Settings":
            root.configure(bg="black")
            settings_frame.configure(bg="black")
            settings_button.configure(bg="black")
            clock_button.configure(bg="black")
            instagram_button.configure(bg="black")
            weather_button.configure(bg="black")
            refresh_token_button.configure(text="Refresh Token", command=refresh_token)
            qrcode_image_label.place_forget()
            stop_server()
        active_transition = animate_transition(old_screen, current_screen, 0)

def animate_transition(old_screen, current_screen, offset):
    global carousel_update_process, active_transition
    if offset > display_height:
        forget_old_screen()
    elif offset == 0:
        if old_screen is not None:
            for item in page_frames[old_screen]:
                item['frame'].place(x=item['x'], y=item['y']-offset, width=item['width'], height=item['height'])
        for item in page_frames[current_screen]:
            item['frame'].place(x=item['x'], y=item['y']+display_height-offset, width=item['width'], height=item['height'])
        active_transition = root.after(15, animate_transition, old_screen, current_screen, offset + 2)
    else:
        if old_screen is not None:
            for item in page_frames[old_screen]:
                item['frame'].place_configure(y=item['y']-offset)
        for item in page_frames[current_screen]:
            item['frame'].place_configure(y=item['y']+display_height-offset)
        active_transition = root.after(15, animate_transition, old_screen, current_screen, offset + 2)

def forget_old_screen():
    global carousel_update_process, old_screen
    if old_screen is not None:
        for item in page_frames[old_screen]:
            item['frame'].place_forget() 
        old_screen = None
    carousel_update_process = root.after(1000 * int(os.getenv('PAGE_TRANSITION_TIME')), start_carousel) if os.getenv('CAROUSEL') != "false" else None

def check_thread_status(thread):
    if thread.is_alive():
        print("Waiting for Token")
        root.after(1000, check_thread_status, thread)
    else:
        thread.join()
        dotenv.load_dotenv()
        instagram_button.config(state=tk.NORMAL)
        switch_to_clock()

def refresh_token():
    auth_url = get_auth_url()
    qrcode_image = create_qrcode(auth_url)
    refresh_token_button.configure(command=lambda: local_browser_capture(auth_url), text="Open Browser")
    qrcode_image_label.configure(image=qrcode_image)
    qrcode_image_label.image = qrcode_image
    qrcode_image_label.place(x=1000, y=85, width=250, height=250)

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

def on_closing():
    stop_server()
    print("Window is closing...")
    root.destroy()

def get_local_ip():
    # Create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Connect to an external server (Google's DNS server)
        s.connect(("8.8.8.8", 80))
        # Get the local IP address
        local_ip = s.getsockname()[0]
    except Exception as e:
        print("Error:", e)
        local_ip = None
    finally:
        s.close()  # Close the socket
    return local_ip

# Create and set variables
initialize_environment()
carousel_update_process = None
clock_refresh_process = None
instagram_refresh_process = None
weather_refresh_process = None
current_screen = None
active_transition = None
text_font = os.getenv("TEXT_FONT")
display_width = int(os.getenv("DISPLAY_WIDTH"))
display_height = int(os.getenv("DISPLAY_HEIGHT"))

# Root initialization
root = tk.Tk()
root.geometry(str(display_width) + 'x' + str(display_height))
root.title("Smart Display")
root.attributes('-fullscreen', False if os.getenv('FULLSCREEN') == "false" else True)
root.configure(bg="black", cursor="none")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Images
cog_image_large = fit_image_to_widget(os.path.join("images","Cog.png"),250,250)
cog_image_small = fit_image_to_widget(os.path.join("images","Cog.png"),50,50)
clock_image_large = fit_image_to_widget(os.path.join("images","Clock.png"),250,250)
clock_image_small = fit_image_to_widget(os.path.join("images","Clock.png"),50,50)
weather_image_large = fit_image_to_widget(os.path.join("images","Weather.png"),250,250)
weather_image_small = fit_image_to_widget(os.path.join("images","Weather.png"),50,50)
camera_image_large = fit_image_to_widget(os.path.join("images","Camera.png"),250,250)
camera_image_small = fit_image_to_widget(os.path.join("images","Camera.png"),50,50)

# Navigation buttons
# Variables
vertical_margin_right = 10
button_size = 50
vertical_margin_top = 15
vertical_margin_bottom = 15
total_button_height = button_size * 4
total_vertical_spacing = vertical_margin_top + vertical_margin_bottom
available_vertical_space = display_height - total_button_height - total_vertical_spacing
vertical_spacing = available_vertical_space / (4 - 1)
# Buttons
settings_button = tk.Button(root, image=cog_image_small, bg="black", fg="black", activebackground="grey", width=button_size, height=button_size, command=switch_to_settings, bd=0, highlightthickness=0)
settings_button.place(x=display_width-button_size-vertical_margin_right,y=(button_size + vertical_spacing) * 0 + vertical_margin_top,width=button_size,height=button_size)
clock_button = tk.Button(root, image=clock_image_small, bg="black", fg="black", activebackground="grey", width=button_size, height=button_size, command=switch_to_clock, bd=0, highlightthickness=0)
clock_button.place(x=display_width-button_size-vertical_margin_right,y=(button_size + vertical_spacing) * 1 + vertical_margin_top,width=button_size,height=button_size)
instagram_button_state = tk.DISABLED if update_ig_stats() == "No Valid Token" else tk.NORMAL
instagram_button = tk.Button(root, image=camera_image_small, bg="black", fg="black", activebackground="grey", width=button_size, height=button_size, command=switch_to_instagram, bd=0, highlightthickness=0, state=instagram_button_state)
instagram_button.place(x=display_width-button_size-vertical_margin_right,y=(button_size + vertical_spacing) * 2 + vertical_margin_top,width=button_size,height=button_size)
weather_button = tk.Button(root, image=weather_image_small, bg="black", fg="black", activebackground="grey", width=button_size, height=button_size, command=switch_to_weather, bd=0, highlightthickness=0)
weather_button.place(x=display_width-button_size-vertical_margin_right,y=(button_size + vertical_spacing) * 3 + vertical_margin_top,width=button_size,height=button_size)

# Clock widgets
clock_frame = tk.Frame(root, bg="black")
clock_logo = tk.Label(clock_frame, bg="black", fg="white", image=clock_image_large)
clock_logo.place(x=10, y=(display_height-250)/2, width=250, height=250)
clock_label = tk.Label(clock_frame, bg="black", fg="white", font=(text_font, 50), anchor="center", text="Time")
clock_label.place(x=260, y=10, width=1000, height=100)
clock_time = tk.Label(clock_frame, bg="black", fg="white", font=(text_font, 150), anchor="center")
clock_time.place(x=280, y=100, width=920, height=200)
clock_date = tk.Label(clock_frame, bg="black", fg="white", font=(text_font, 50), anchor="center")
clock_date.place(x=1160, y=100, width=180, height=200)

# Instagram widgets
instagram_frame = tk.Frame(root, bg="black")
instagram_logo = tk.Label(instagram_frame, bg="black", fg="white", image=camera_image_large)
instagram_logo.place(x=10, y=(display_height-250)/2, width=250, height=250)
instagram_label = tk.Label(instagram_frame, bg="black", fg="white", font=(text_font, 50), anchor="center", text="Followers")
instagram_label.place(x=260, y=10, width=1000, height=100)
instagram_followers = tk.Label(instagram_frame, bg="black", fg="white", font=(text_font, 125), anchor="center")
instagram_followers.place(x=280, y=100, width=960, height=200)

# Weather widgets
weather_frame = tk.Frame(root, bg="black")
weather_logo = tk.Label(weather_frame, bg="black", fg="white", image=weather_image_large)
weather_logo.place(x=10, y=(display_height-250)/2, width=250, height=250)
weather_label = tk.Label(weather_frame, bg="black", fg="white", font=(text_font, 50), anchor="center", text="Weather")
weather_label.place(x=260, y=10, width=1000, height=100)
weather_now_label = tk.Label(weather_frame, bg="black", fg="white", font=(text_font, 30), anchor="center", text="Now")
weather_now_label.place(x=260, y=100, width=480, height=50)
weather_now_temp = tk.Label(weather_frame, bg="black", fg="white", font=(text_font, 70), anchor="center")
weather_now_temp.place(x=260, y=155, width=480, height=80)
weather_now_conditions = tk.Label(weather_frame, bg="black", fg="white", font=(text_font, 25), anchor="center", wraplength=480)
weather_now_conditions.place(x=260, y=235, width=480, height=80)
weather_future_label = tk.Label(weather_frame, bg="black", fg="white", font=(text_font, 30), anchor="center")
weather_future_label.place(x=760, y=100, width=480, height=50)
weather_future_temp = tk.Label(weather_frame, bg="black", fg="white", font=(text_font, 70), anchor="center")
weather_future_temp.place(x=760, y=155, width=480, height=80)
weather_future_conditions = tk.Label(weather_frame, bg="black", fg="white", font=(text_font, 25), anchor="center", wraplength=480)
weather_future_conditions.place(x=760, y=235, width=480, height=80)

# Settings widgets
settings_frame = tk.Frame(root, bg="black")
settings_logo = tk.Label(settings_frame, bg="#505050", fg="white", image=cog_image_large)
settings_logo.place(x=10, y=(display_height-250)/2, width=250, height=250)
settings_label = tk.Label(settings_frame, bg="#505050", fg="white", font=(text_font, 50), anchor="center", text="Settings")
settings_label.place(x=260, y=10, width=1000, height=100)
close_window_button = tk.Button(settings_frame, text="Close App", bg="#505050", fg="white",activebackground="grey", activeforeground="white", font=(text_font, 20), command=on_closing, bd=1, highlightthickness=1)
close_window_button.place(x=300, y=35, width=200, height=50)
ip_address_label = tk.Label(settings_frame, bg="#505050", fg="white", font=(text_font, 13), anchor="center")
ip_address_label.place(x=760 , y=130, width=250, height=25)
token_label = tk.Label(settings_frame, bg="#505050", fg="white", font=(text_font, 20), anchor="center", text="Token Has X\nDays Remaining")
token_label.place(x=760, y=160, width=250, height=75)
refresh_token_button = tk.Button(settings_frame, text="Refresh Token", bg="#505050", fg="white",activebackground="grey", activeforeground="white", font=(text_font, 20), command=refresh_token, bd=1, highlightthickness=1)
refresh_token_button.place(x=785, y=240, width=200, height=50)
carousel_stop_start_label = tk.Label(settings_frame, bg="#505050", fg="white", font=(text_font, 18), anchor="center", text="Carousel is Running")
carousel_stop_start_label.place(x=300, y=110, width=300, height=50)
carousel_stop_start_button = tk.Button(settings_frame, text="Stop", bg="#505050", fg="white",activebackground="grey", activeforeground="white", font=(text_font, 20), command=carousel_stop_start, bd=1, highlightthickness=1)
carousel_stop_start_button.place(x=625, y=115, width=100, height=40)
page_transition_start_stop_label = tk.Label(settings_frame, bg="#505050", fg="white", font=(text_font, 18), anchor="center", text="Page Transitions are On")
page_transition_start_stop_label.place(x=300, y=160, width=300, height=50)
page_transition_start_stop_button = tk.Button(settings_frame, text="Stop", bg="#505050", fg="white",activebackground="grey", activeforeground="white", font=(text_font, 20), command=page_transition_stop_start, bd=1, highlightthickness=1)
page_transition_start_stop_button.place(x=625, y=165, width=100, height=40)
page_transition_time_label = tk.Label(settings_frame, bg="#505050", fg="white", font=(text_font, 18), anchor="center", text="Carousel Time:")
page_transition_time_label.place(x=300, y=210, width=250, height=50)
validation = root.register(validate_input)
page_transition_time_var = tk.StringVar()
page_transition_time_entry = tk.Entry(settings_frame, textvariable=page_transition_time_var , validate="key",validatecommand=(validation, '%P') , bg="#505050", fg="white", justify="center", font=(text_font, 20), bd=1, highlightthickness=1)
page_transition_time_entry.place(x=560, y=215, width=50, height=40)
page_transition_time_button = tk.Button(settings_frame, text="Submit", bg="#505050", fg="white",activebackground="grey", activeforeground="white", font=(text_font, 20), command=page_transition_time, bd=1, highlightthickness=1)
page_transition_time_button.place(x=620, y=215, width=110, height=40)
page_transition_time_decrease_button = tk.Button(settings_frame, text="<", bg="#505050", fg="white",activebackground="grey", activeforeground="white", font=(text_font, 20), command=page_transition_time_decrease, bd=1, highlightthickness=1)
page_transition_time_decrease_button.place(x=555, y=260, width=30, height=40)
page_transition_time_increase_button = tk.Button(settings_frame, text=">", bg="#505050", fg="white",activebackground="grey", activeforeground="white", font=(text_font, 20), command=page_transition_time_increase, bd=1, highlightthickness=1)
page_transition_time_increase_button.place(x=585, y=260, width=30, height=40)
qrcode_image_label = tk.Label(settings_frame, bg="#505050", fg="#505050")

page_frames = {
    'Clock': [
        {'frame': clock_frame, 'width': display_width-button_size-vertical_margin_right, 'height': display_height, 'x': 0, 'y': 0}
    ],
    'Instagram': [
        {'frame': instagram_frame, 'width': display_width-button_size-vertical_margin_right, 'height': display_height, 'x': 0, 'y': 0}
    ],
    'Weather': [
        {'frame': weather_frame, 'width': display_width-button_size-vertical_margin_right, 'height': display_height, 'x': 0, 'y': 0}
    ],
    'Settings': [
        {'frame': settings_frame, 'width': display_width-button_size-vertical_margin_right, 'height': display_height, 'x': 0, 'y': 0}
    ]
}

start_carousel()
root.mainloop()