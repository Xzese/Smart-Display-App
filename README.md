# Smart Display App

<p align="center">
  <a href="https://github.com/Xzese/Smart-Display-App/stargazers"><img src="https://img.shields.io/github/stars/Xzese/Smart-Display-App?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/Xzese/Smart-Display-App/commits/main"><img src="https://img.shields.io/github/last-commit/Xzese/Smart-Display-App?style=flat-square" alt="Last commit"></a>
  <a href="https://github.com/Xzese/Smart-Display-App"><img src="https://img.shields.io/github/languages/top/Xzese/Smart-Display-App?style=flat-square" alt="Top language"></a>
</p>

This application runs a smart display that shows screens for the time, Instagram followers, and weather. To use the app, follow the instructions below.

## Navigation Icons

The application utilizes three image assets for navigation icons:

- **Settings Menu**: Represents the settings menu screen.
- **Clock**: Represents the time screen.
- **Instagram**: Represents the Instagram screen.
- **Weather**: Represents the weather screen.

These icons enhance the user experience by providing visual cues for navigating between different screens.

## Setting Up the App

Before running the application, follow these steps to set up the required environment variables and create the Facebook Development App:

### Creating the Facebook Development App

1. Go to the [Facebook Developer Dashboard](https://developers.facebook.com/) and log in with your Facebook account.
2. Click on "My Apps" and then "Create App".
3. Choose the "Business" category and click "Next".
4. Fill in the required fields such as the app name, email address, and select a Business Manager account if applicable. Click "Create App".
5. Once the app is created, navigate to the app dashboard.
6. In the app dashboard, navigate to the "Products" section.
7. Click on "Add a Product" and select "Facebook Login".
8. Follow the prompts to configure Facebook Login for your app.
9. After configuring Facebook Login, repeat step 7 and select "Instagram Graph API".
10. Follow the prompts to configure Instagram Graph API for your app.
11. Navigate to the "Settings" tab in the app dashboard.
12. In the "Basic" settings, add the app domain for the device running Smart Display.
13. In the "Facebook Login" settings, add `https://<CLIENT_IP_ADDRESS>:5000/callback` to "Valid OAuth Redirect URIs", replacing the placeholder with the exact value of `CLIENT_IP_ADDRESS` from your `.env` file. The callback uses the local server's ad-hoc TLS certificate, as in the browser login flow.
14. Save your changes. The redirect URI in Facebook settings must match the configured address, scheme, port, and path exactly.

### Setting Up Weather Functionality

To enable weather functionality in the application, follow these steps:

1. Create a free account on [WeatherAPI.com](https://www.weatherapi.com/).
2. Obtain an API key.
3. Add the API key to the `.env` file under the key `WEATHER_API_KEY`.
4. Specify the location for which you want to display weather information. You can use various formats such as UK Postcode, ZIP code, City name, Latitude and Longitude coordinates, etc.
5. Add the location information to the `.env` file under the key `WEATHER_LOCATION`.
6. Once these environment variables are set up, the application will use the WeatherAPI to fetch weather data for the specified location and display it on the weather screen.

### Setting Environment Variables

1. Create a `.env` file in the project directory.
2. Set the following environment variables in the `.env` file:
   - `APP_ID`: The App ID obtained from the Facebook Developer Dashboard.
   - `APP_SECRET`: The App Secret obtained from the Facebook Developer Dashboard.
   - `CLIENT_TOKEN`: The Client Token obtained from the Facebook Developer Dashboard.
   - `WEATHER_API_KEY`: A WeatherAPI.com API key obtained from [WeatherAPI.com](https://www.weatherapi.com/). You can sign up for a free account to obtain the API key.
   - `CLIENT_IP_ADDRESS`: The address of the device where the application will run, such as `192.168.x.y`, `localhost`, or `127.0.0.1`. This value must match the host in the Facebook redirect URI, `https://<CLIENT_IP_ADDRESS>:5000/callback`.
   - `GRAPH_API_VERSION` (optional): The Graph API version to use for both Instagram requests, for example `v26.0`. When unset or blank, the app uses `v26.0`.

Ensure that the `.env` file contains these variables with their respective values before running the application. These variables are necessary for the application to communicate with the Facebook Graph API and WeatherAPI.com services.

## Generating Access Token

To obtain an access token, follow these steps:

1. Go to the settings menu.
2. It will show the amount of time remaining on the access token.
3. Click the "Refresh Token" button.
4. It will generate a QR code that can be scanned using another device on the local network and authenticated with Facebook.
5. Alternatively, click the "Open Browser" button to log in on the device natively.

**Note:** The website may display a warning that it's not secure, as it uses adhoc SSL certificates.

The application starts a local callback server on port 5000 during login. It stops when login finishes or when you leave the Settings page. The returned OAuth access token and expiry are saved to `.env`; the application does not perform a separate exchange for a long-lived token. A denied login, timeout, or other failure leaves the app in Settings with a message and a retry option.

## Instagram Functionality

The Instagram functionality displays the follower count of your Instagram account.

- The follower count is refreshed every 20 seconds while the Instagram screen is active.
- When the follower count increases, the display flashes green every other second until the next update.
- When the follower count decreases, the display flashes red every other second until the next update.
- If the follower count remains the same, the display remains white until the next update.

This functionality provides real-time feedback on changes in your Instagram follower count, enhancing the user experience.

## Weather Functionality

The weather functionality is based on data from [WeatherAPI.com](https://www.weatherapi.com/).

The weather information displayed includes the current temperature and conditions, as well as the forecast. The forecast varies depending on the current time:

- Before 10:00 AM: Shows the weather forecast for 12:00 PM.
- After 10:00 AM and before 4:00 PM: Shows the forecast for 6:00 PM.
- After 4:00 PM: Shows the forecast for 12:00 PM of the following day.
- After 12:00 AM: Shows the forecast for 12:00 PM of the same day.

The application fetches weather data based on the specified location and displays it on the weather screen. Ensure that the `.env` file contains the required environment variables for accessing the WeatherAPI.com service.

## Validation

Initialize the pinned helper with `git submodule update --init --recursive`, install `requirements.txt`, then run `python -m unittest discover -s tests`. The tests exercise the app entry point with headless UI and provider fixtures, including unsuccessful login retries, stale results after navigation and both Instagram request URLs. They do not perform live Meta authentication or validate graphical layout.
