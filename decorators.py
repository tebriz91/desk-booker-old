from collections import Counter
from telegram import Update
from telegram.ext import CallbackContext
import config
from logger import Logger
from db_queries import execute_db_query

logger = Logger.get_logger(__name__)

# Global counter for command usage
command_usage_counter = Counter()

async def is_admin(user_id):
    
    # Check if the user is the superadmin (defined in config.py)
    if user_id == config.ADMIN_USER_ID:
        return True

    # Check if the user is an admin (is_admin = 1 in the database)
    try:
        result = await execute_db_query("SELECT is_admin FROM users WHERE user_id = ?", (user_id,), fetch_one=True)
        return result and result[0] == 1
    
    except Exception as e:
        logger.error(f"Error checking admin status for user {user_id}: {e}")

        return False # Default to non-admin in case of an error

def superadmin_required(func):
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            user_id = str(update.effective_user.id)

            logger.info(f"Superadmin command '{func.__name__}' invoked by {user_id}")

            if user_id != config.ADMIN_USER_ID:

                logger.info(f"Unauthorized superadmin access attempt by {user_id} for command {func.__name__}")

                await update.message.reply_text("You are not authorized to use this command.")

                return

            return await func(update, context, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error in superadmin_required decorator: {e}")
            await update.message.reply_text("An error occurred. Please try again later.")
    
    return wrapper

def admin_required(func):
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            user_id = str(update.effective_user.id)

            logger.info(f"Admin command '{func.__name__}' invoked by {user_id}")

            if not await is_admin(user_id):

                logger.info(f"Unauthorized admin access attempt by {user_id} for command {func.__name__}")

                await update.message.reply_text("You are not authorized to use this command.")

                return

            return await func(update, context, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error in admin_required decorator: {e}")
            await update.message.reply_text("An error occurred. Please try again later.")
    
    return wrapper

def user_required(func):
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            user_id = str(update.effective_user.id)

            logger.info(f"User command '{func.__name__}' invoked by {user_id}")

            result = await execute_db_query("SELECT user_id FROM users WHERE user_id = ?", (user_id,), fetch_one=True)

            if not result:

                logger.info(f"Unregistered user {user_id} attempted to use command {func.__name__}")

                await update.message.reply_text("You need to be registered to use this command. Use /start to register.")

                return

            return await func(update, context, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error in user_required decorator: {e}")
            await update.message.reply_text("An error occurred. Please try again later.")
        
    return wrapper

def track_command_usage(func):
    async def wrapper(update, context, *args, **kwargs):
        if update.message and update.message.text:
            command = update.message.text.split()[0]
            command_usage_counter[command] += 1
        return await func(update, context, *args, **kwargs)

    return wrapper

@superadmin_required
async def view_command_stats(update, context):
    stats_message = "Command Usage Stats:\n\n"
    for command, count in command_usage_counter.items():
        stats_message += f"{command}: {count}\n"
    await update.message.reply_text(stats_message)

# Usage in other modules:
# from decorators import admin_required, user_required
