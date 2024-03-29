# Smart Display App

This application runs a smart display that shows screens for the time, Instagram followers, and weather. To use the app, follow the instructions below.

## Generating Access Token

To obtain an access token, follow these steps:

1. Create a Business Development App on Facebook.
2. Add the Instagram Graph API product to your app.
3. Visit the [Facebook Graph Explorer](https://developers.facebook.com/tools/explorer/).
4. Select your app from the "Application" dropdown menu.
5. Click on "Get Token" and choose "Get User Access Token".
6. Select the required permissions/scope:
   - `pages_show_list`
   - `business_management`
   - `instagram_basic`
   - `instagram_manage_insights`
7. Click "Generate Access Token" and copy the token.

## Running the Application

Once you've obtained the access token:

1. Paste it into the `.env` file as `SHORT_ACCESS_TOKEN`.
2. Run the application using the appropriate command (e.g., `python main.py`).

## Note on Access Token

The generated token is short-lived and may expire after a certain period. To ensure continuous functionality, the code utilizes the short-lived token to obtain a long-lived token from the Facebook Graph API, which lasts for 60 days.

For detailed instructions on generating and using access tokens, refer to the Facebook Graph API documentation.

## Navigation Icons

The application utilizes three image assets for navigation icons:

- **Camera**: Represents the Instagram screen.
- **Clock**: Represents the time screen.
- **Weather**: Represents the weather screen.

These icons enhance the user experience by providing visual cues for navigating between different screens.

## Weather Functionality

The weather functionality is based on data from [WeatherAPI.com](https://www.weatherapi.com/). To enable weather display:

1. Create a free account on WeatherAPI.com.
2. Obtain an API key.
3. Add the API key to the `.env` file under the key `WEATHER_API_KEY`.
4. Specify the location (e.g., UK Postcode, ZIP code, city) in the `.env` file under the key `WEATHER_LOCATION`.
5. The weather information displayed is for 12:00 if the time is before, for 18:00 if time is 12:00-17:59 and for tomorrow 12:00 if the time is 18:00 onwards.