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

To run the application:

1. If the `.env` file does not already contain a `SHORT_ACCESS_TOKEN`, the application will prompt you to enter the access token in the terminal.
2. After entering the access token, the application will use it to exchange for a Long Lived Access Token.
3. If the Short Lived Access Token hasn't expired, the Long Lived Access Token will be saved as `LONG_ACCESS_TOKEN` in the `.env` file.
4. If the Short Lived Access Token has expired, it will be deleted from the `.env` file, and the application will prompt you again for another access token.
5. Once the access token is obtained and saved in the `.env` file, the application will proceed to run the tkinter display.

## Note on Access Token

The generated token is short-lived and may expire after a certain period. To ensure continuous functionality, the code utilizes the short-lived token to obtain a long-lived token from the Facebook Graph API, which lasts for 60 days.

For detailed instructions on generating and using access tokens, refer to the Facebook Graph API documentation.

## Navigation Icons

The application utilizes three image assets for navigation icons:

- **Clock**: Represents the time screen.
- **Instagram**: Represents the Instagram screen.
- **Weather**: Represents the weather screen.

These icons enhance the user experience by providing visual cues for navigating between different screens.

## Weather Functionality

The weather functionality is based on data from [WeatherAPI.com](https://www.weatherapi.com/). To enable weather display:

1. Create a free account on WeatherAPI.com.
2. Obtain an API key.
3. Add the API key to the `.env` file under the key `WEATHER_API_KEY`.
4. Specify the location (e.g., UK Postcode, ZIP code, City, Latitude, Longitude, etc.) in the `.env` file under the key `WEATHER_LOCATION`.
5. The weather information displayed includes the current temperature and conditions, as well as the forecast. The forecast varies depending on the current time:
   - Before 10:00 AM: Shows the weather forecast for 12:00 PM.
   - After 10:00 AM and before 4:00 PM: Shows the forecast for 6:00 PM.
   - After 4:00 PM: Shows the forecast for 12:00 PM of the following day.
   - After 12:00 AM: Shows the forecast for 12:00 PM of the same day.