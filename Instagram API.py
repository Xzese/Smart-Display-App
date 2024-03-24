import os
import requests
import dotenv
import datetime
import tkinter as tk

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
            os.environ['IG_FOLLOWERS_COUNT'] = str(account_details['followers_count'])
            os.environ['IG_FOLLOWS_COUNT'] = str(account_details['follows_count'])
            os.environ['IG_LAST_UPDATED'] = str(datetime.datetime.now())
            dotenv.set_key('.env',"IG_FOLLOWERS_COUNT", os.environ["IG_FOLLOWERS_COUNT"])
            dotenv.set_key('.env',"IG_FOLLOWS_COUNT", os.environ["IG_FOLLOWS_COUNT"])
            dotenv.set_key('.env',"IG_LAST_UPDATED", os.environ["IG_LAST_UPDATED"])
        else:
            # Print the error message if the request was not successful
            print("Error Update IG Stats:", response.text)
            return None

    print("Followers: " + os.environ['IG_FOLLOWERS_COUNT'] + "\nFollowing: " + os.environ['IG_FOLLOWS_COUNT'])
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

#print(update_ig_stats())
        
screen_update_id = None

def switch_to_clock():
    global screen_update_id
    if screen_update_id:
        root.after_cancel(screen_update_id)
    pagelabel.configure(text="Time")
    update_clock()

def update_clock():
    global screen_update_id
    pagevalue.configure(text=datetime.datetime.now().strftime("%H:%M:%S"), font=("Arial", 150))
    screen_update_id = root.after(500, update_clock)

def switch_to_instagram():
    global screen_update_id
    if screen_update_id:
        root.after_cancel(screen_update_id)
    pagelabel.configure(text="Followers")
    pagevalue.configure(text=os.getenv('IG_FOLLOWERS_COUNT'), font=("Arial", 150))
    update_instagram()

def update_instagram():
    global screen_update_id
    update_ig_stats()
    pagevalue.configure(text=os.getenv('IG_FOLLOWERS_COUNT'))
    screen_update_id = root.after(1000 * 5, update_instagram)

def switch_to_weather():
    global screen_update_id
    if screen_update_id:
        root.after_cancel(screen_update_id)
    pagelabel.configure(text="Weather")
    pagevalue.configure(text='10C, Rainy', font=("Arial", 100))

# Create the main window
root = tk.Tk()
root.geometry("1400x320")

root.configure(bg="black")

# Create and place widgets using the grid layout
screenlogo = tk.Label(root, text="Logo", bg="black", fg="white", font=("Arial", 32))
screenlogo.grid(row=0, column=0, sticky="nsw", rowspan=3, padx=(0, 0))

pagelabel = tk.Label(root, text="Followers", bg="black", fg="white", font=("Arial", 50))
pagelabel.grid(row=0, column=1, sticky="nsew", columnspan=7, pady=(0, 0))

pagevalue = tk.Label(root, text=os.getenv('IG_FOLLOWERS_COUNT'), bg="black", fg="white", font=("Arial", 150))
pagevalue.grid(row=1, column=1, sticky="nsew", rowspan=2, columnspan=7, pady=(0, 0))

clockimage = tk.PhotoImage(file=os.path.join("images","Clock.png")).subsample(10)
clockbutton = tk.Button(root, image=clockimage, bg="black", width=50, height=50, command=switch_to_clock, bd=0, highlightthickness=0)
clockbutton.grid(row=0, column=9, sticky="ne", pady=(10,0), padx=(0, 10))

cameraimage = tk.PhotoImage(file=os.path.join("images","Camera.png")).subsample(10)
instagrambutton = tk.Button(root, image=cameraimage, bg="black", width=50, height=50, command=switch_to_instagram, bd=0, highlightthickness=0)
instagrambutton.grid(row=1, column=9, sticky="e", padx=(0, 10))

weatherimage = tk.PhotoImage(file=os.path.join("images","Weather.png")).subsample(5)
weatherbutton = tk.Button(root, image=weatherimage, bg="black", width=50, height=50, command=switch_to_weather, bd=0, highlightthickness=0)
weatherbutton.grid(row=2, column=9, sticky="se", pady=(0,10), padx=(0, 10))

# Configure row and column sizes
root.rowconfigure(0, weight=1, minsize=100)
root.rowconfigure(1, weight=1, minsize=100)
root.rowconfigure(2, weight=1, minsize=100)
for x in range(0,8):
    root.columnconfigure(x, weight=1, minsize=100)
root.columnconfigure(9, weight=1, minsize=25)

# Run the Tkinter event loop
root.mainloop()

root.after(1000, update_instagram)