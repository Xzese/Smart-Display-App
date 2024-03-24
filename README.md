# Smart Display App

This application runs a smart display that shows screens for the time, Instagram followers, and weather (currently weather is static as hasn't been implemented). To use the app, follow the instructions below.

## Generating Access Token

To generate an access token:

1. Visit the [Facebook Graph Explorer](https://developers.facebook.com/tools/explorer/).
2. Select your app from the "Application" dropdown menu.
3. Click on "Get Token" and select "Get User Access Token".
4. Choose the required permissions/scope:
   - `pages_show_list`
   - `business_management`
   - `instagram_basic`
   - `instagram_manage_insights`
5. Click "Generate Access Token" and copy the token.

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
