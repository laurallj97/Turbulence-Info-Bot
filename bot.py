from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import datetime
import numpy as np
import xarray as xr
import re
import os

from main import (
    download_era5_data,
    calculate_wind_shear,
    plot_wind_shear,
    calculate_horizontal_shear,
    calculate_general_wind_shear,
    classify_turbulence,
    plot_turbulence_level
)

# Constants for the Telegram bot
TOKEN : Final = os.environ["TOKEN_TELEGRAM"]
BOT_USERNAME : Final = os.environ["BOT_USERNAME"]

# Function to generate general wind shear data
def get_windshear_data(date, time, continent):
    """
    Fetches and processes wind shear data for a given date, time, and continent.

    Args:
        date (str): The date in 'YYYY-MM-DD' format.
        time (str): The time in 'HH:MM' format.
        continent (str): The name of the continent.

    Returns:
        str: Path to the generated wind shear image.
    """
    # Define continent boundaries
    continent_boundaries = {
    'Africa': [37.38, -18.03, -34.83, 51.48],
    'Antarctica': [-60.00, -180.00, -90.00, 180.00],
    'Asia': [77.71, 25.98, -11.02, 179.69],
    'Australia': [-10.07, 112.92, -43.63, 159.11],
    'Europe': [71.00, -31.00, 36.00, 40.00],
    'North America': [83.17, -168.69, 14.53, -52.62],
    'South America': [13.40, -81.30, -55.96, -34.76]

    }
    # Get continent boundaries or default to Europe
    continent = continent_boundaries.get(continent, [71.0, -31.0, 36.0, 40.0])

    # Download ERA5 data
    data = download_era5_data(date, time, continent)

    # Calculate and plot vertical wind shear
    vertical_shear = calculate_wind_shear(data)
    plot_wind_shear(vertical_shear, 'Vertical Wind Shear', 'vertical_wind_shear.png', continent)

    # Calculate and plot horizontal wind shear  
    horizontal_shear = calculate_horizontal_shear(data)
    plot_wind_shear(horizontal_shear, 'Horizontal Wind Shear', 'horizontal_wind_shear.png',continent)

    # Calculate and plot general wind shear
    general_wind_shear = calculate_general_wind_shear(vertical_shear, horizontal_shear)
    plot_wind_shear(general_wind_shear, 'General Wind Shear (Vertical + Horizontal)', 'general_wind_shear.png', continent)

    return 'general_wind_shear.png'

# Function to fetch or generate turbulence data
def get_turbulence_data(date, time, continent):
    """
    Fetches and processes turbulence data for a given date, time, and continent.

    Args:
        date (str): The date in 'YYYY-MM-DD' format.
        time (str): The time in 'HH:MM' format.
        continent (str): The name of the continent.

    Returns:
        str: Path to the generated turbulence level image.
    """

    # Define continent boundaries
    continent_boundaries = {
    'Africa': [37.38, -18.03, -34.83, 51.48],
    'Antarctica': [-60.00, -180.00, -90.00, 180.00],
    'Asia': [77.71, 25.98, -11.02, 179.69],
    'Australia': [-10.07, 112.92, -43.63, 159.11],
    'Europe': [71.00, -31.00, 36.00, 40.00],
    'North America': [83.17, -168.69, 14.53, -52.62],
    'South America': [13.40, -81.30, -55.96, -34.76]

    }
    # Get continent boundaries or default to Europe
    continent = continent_boundaries.get(continent, [71.0, -31.0, 36.0, 40.0])
    
    # Download ERA5 data
    data = download_era5_data(date, time, continent)

    # Calculate and plot vertical wind shear
    vertical_shear = calculate_wind_shear(data)
    plot_wind_shear(vertical_shear, 'Vertical Wind Shear', 'vertical_wind_shear.png', continent)

    # Calculate and plot horizontal wind shear
    horizontal_shear = calculate_horizontal_shear(data)
    plot_wind_shear(horizontal_shear, 'Horizontal Wind Shear', 'horizontal_wind_shear.png',continent)
    
    # Calculate and plot general wind shear
    general_wind_shear = calculate_general_wind_shear(vertical_shear, horizontal_shear)
    plot_wind_shear(general_wind_shear, 'General Wind Shear (Vertical + Horizontal)', 'general_wind_shear.png', continent)

    # Classify turbulence and plot turbulence level
    turbulence = np.vectorize(classify_turbulence)(general_wind_shear)
    turbulence_data = xr.DataArray(turbulence, coords=[general_wind_shear['latitude'], general_wind_shear['longitude']], dims=['latitude', 'longitude'])
    plot_turbulence_level(turbulence_data, 'turbulence_level.png',continent)

    return 'turbulence_level.png'


# Define the command handlers

# Start command to introduce the user to the Bot
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command. Sends a welcome message to the user.
    """
    await update.message.reply_text('Welcome to TurbulenceInfoBot! 🌪️\nI provide valuable information on turbulence and wind shear based on ERA5 data. While the data is comprehensive, please note that it may not be the most recent.\nUse the following commands to get the most recent turbulence and wind shear images:\n- /turbulence_request [date] [time] [continent] - Request turbulence data for a specific date, time, and continent.\n- /windshear_request [date] [time] [continent] - Request wind shear data for a specific date, time, and continent.\n- /help - Get help on how to use the bot.\nStay safe and informed! ✈️')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /help command. Provides information on available commands.
    """
    await update.message.reply_text('Here are the available commands to help you stay informed about turbulence and wind shear:\n- /turbulence_request [date] [time] [continent] - Request turbulence data for a specific date, time, and continent.\n- /windshear_request [date] [time] [continent] - Request wind shear data for a specific date, time, and continent.\n- /about - Learn more about the bot.\n- /latest - Get the latest images available.\n- /continent [continent] - Get images for a specific continent.\nIf you have any questions or need further assistance, feel free to ask! 🌐')

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /about command. Provides information about the bot.
    """
    await update.message.reply_text('TurbulenceInfoBot uses the latest meteorological data from ERA5 to provide turbulence and wind shear information through images. This helps users stay informed about weather conditions, ensuring safer flights and better planning.\nPlease note that while the data is comprehensive, it may not be the most recent.\nStay informed and fly safe! 🛫')

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /latest command. Retrieves the latest turbulence and wind shear data.
    """
    await update.message.reply_text("Retrieving ERA5 meteorological data...")
    
    date = datetime.datetime.now()
    time = datetime.datetime.now().time()
    continent = 'Europe'  # Default continent
    try: 
        turbulence_image = get_turbulence_data(date, time, continent)
        windshear_image = get_windshear_data(date, time, continent)
    except Exception as e:
        error_message = str(e)
        match = re.search(r'The latest date available for this dataset is: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})', error_message)
        if match:
            latest_date_str = match.group(1)
            await update.message.reply_text(f"The requested date is not available yet. because ERA5 data is updated daily with a latency of about 5 days. Retrieving the latest available data for {latest_date_str}...")
            latest_date = datetime.datetime.strptime(latest_date_str, '%Y-%m-%d %H:%M')
            date = latest_date.date()
            time = latest_date.time()
            turbulence_image = get_turbulence_data(date, time, continent)
            windshear_image = get_windshear_data(date, time, continent)
        else:
            await update.message.reply_text(f"An error occurred: {error_message}")
            return
    await update.message.reply_photo(open(turbulence_image, 'rb'))
    await update.message.reply_photo(open(windshear_image, 'rb'))
    
async def continent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /continent command. Retrieves data for a specific continent.
    """
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Retrieving ERA5 meteorological data...")
        await update.message.reply_text("Please provide the continent name.")
        return
    continent_name = ' '.join(args)
    date = datetime.datetime.now()
    time = datetime.datetime.now().time()
    turbulence_image = get_turbulence_data(date, time, continent_name)
    await update.message.reply_photo(open(turbulence_image, 'rb'))

async def turbulence_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /turbulence_request command. Retrieves turbulence data for a specific date, time, and continent.
    """
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Please provide the date, time, and continent in the format: /turbulence_request YYYY-MM-DD HH:MM Continent")
            return
        await update.message.reply_text("Retrieving ERA5 meteorological data...")
        date_str = args[0]
        time_str = args[1]
        continent = ' '.join(args[2:])

        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            time = datetime.datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            await update.message.reply_text("Invalid date or time format. Please use YYYY-MM-DD for date and HH:MM for time.")
            return

        turbulence_image = get_turbulence_data(date, time, continent)

        await update.message.reply_photo(open(turbulence_image, 'rb'))

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

def handle_response(text:str) -> str:
    """
    Handles the response for unrecognized messages.
    """
    return "I can only provide turbulence data for a specific date, time, and continent. If you want to do that type /turbulence_request"

async def windshear_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /windshear_request command. Retrieves wind shear data for a specific date, time, and continent.
    """
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Please provide the date, time, and continent in the format: /windshear_request YYYY-MM-DD HH:MM Continent")
            return
        await update.message.reply_text("Retrieving ERA5 meteorological data...")
        date_str = args[0]
        time_str = args[1]
        continent = ' '.join(args[2:])

        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            time = datetime.datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            await update.message.reply_text("Invalid date or time format. Please use YYYY-MM-DD for date and HH:MM for time.")
            return

        windshear_image = get_windshear_data(date, time, continent)

        await update.message.reply_photo(open(windshear_image, 'rb'))

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

def handle_response(text:str) -> str:
    """
    Handles the response for unrecognized messages.
    """
    return "I can only provide turbulence/wind shear data for a specific date, time, and continent. If you want to do that type /turbulence_request or /windshear_request"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles incoming messages and provides a response.
    """
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User ({update.message.chat.id}) in {message_type}: '{text}'")

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
        
    else:
        response: str = handle_response(text)

    print("Bot:", response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles errors that occur during bot operation.
    """
    print(f"Update {update} caused error {context.error}")

print("Starting bot...")
app = Application.builder().token(TOKEN).build()

# Commands
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("latest", latest))
app.add_handler(CommandHandler("continent", continent))
app.add_handler(CommandHandler("turbulence_request", turbulence_request))
app.add_handler(CommandHandler("windshear_request", windshear_request))

# Messages
app.add_handler(MessageHandler(filters.TEXT, handle_message))

# Errors
app.add_error_handler(error)

# Polls the bot
print('Polling...')
app.run_polling(poll_interval=3)
