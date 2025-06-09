import asyncio
from collections import defaultdict
from telegram import Update, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio, InputMediaAnimation
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config import BOT_TOKEN, REPLACEMENT_LINK, logger
from link_replacer import LinkReplacer

class TelegramLinkSwapBot:
    def __init__(self):
        self.link_replacer = LinkReplacer(REPLACEMENT_LINK)
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.media_groups = defaultdict(list)  # Store media groups by chat_id
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Message handlers for different content types
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo_message))
        self.application.add_handler(MessageHandler(filters.VIDEO, self.handle_video_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document_message))
        self.application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio_message))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
        self.application.add_handler(MessageHandler(filters.VIDEO_NOTE, self.handle_video_note_message))
        self.application.add_handler(MessageHandler(filters.Sticker.ALL, self.handle_sticker_message))
        self.application.add_handler(MessageHandler(filters.ANIMATION, self.handle_animation_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "🔗 **Link Swap Bot**\n\n"
            "Welcome! I can help you replace links in your messages.\n\n"
            "**How it works:**\n"
            "• Send me any message with links\n"
            "• I'll replace all links with your specified link\n"
            "• Media and text content will be preserved\n\n"
            "**Supported content:**\n"
            "• Text messages\n"
            "• Photos with captions\n"
            "• Videos with captions\n"
            "• Documents with captions\n"
            "• Audio files with captions\n"
            "• And more!\n\n"
            f"**Current replacement link:**\n`{REPLACEMENT_LINK}`\n\n"
            "Just send me a message and I'll process it for you! 🚀"
        )
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"User {update.effective_user.id} started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = (
            "🔗 **Link Swap Bot - Help**\n\n"
            "**Commands:**\n"
            "• `/start` - Start the bot and see welcome message\n"
            "• `/help` - Show this help message\n"
            "• `/status` - Check bot status\n\n"
            "**Usage:**\n"
            "1. Send me any message containing links\n"
            "2. I'll automatically detect and replace all links\n"
            "3. You'll receive the modified message back\n\n"
            "**Supported link formats:**\n"
            "• http://example.com\n"
            "• https://example.com\n"
            "• www.example.com\n"
            "• example.com\n"
            "• Shortened URLs (bit.ly, tinyurl, etc.)\n"
            "• Social media links (t.me, discord.gg, etc.)\n\n"
            "**Note:** All media and text content will be preserved exactly as you sent it!"
        )
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"User {update.effective_user.id} requested help")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        status_message = (
            "✅ **Bot Status: Active**\n\n"
            f"**Current replacement link:**\n`{REPLACEMENT_LINK}`\n\n"
            "**Bot capabilities:**\n"
            "• Link detection and replacement ✅\n"
            "• Media preservation ✅\n"
            "• Text content preservation ✅\n"
            "• Multiple link format support ✅\n\n"
            "Ready to process your messages! 🚀"
        )
        
        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"User {update.effective_user.id} checked bot status")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle plain text messages."""
        try:
            original_text = update.message.text
            logger.info(f"Received text message from user {update.effective_user.id}")
            
            # Process the text for link replacement
            processed_text = self.link_replacer.process_text(original_text)
            
            if processed_text != original_text:
                await update.message.reply_text(processed_text)
                logger.info("Text message processed and sent back with replaced links")
            else:
                # Send original text back when no links found
                await update.message.reply_text(original_text)
                logger.info("No links found in text message, sent original back")
        
        except TelegramError as e:
            logger.error(f"Telegram error in handle_text_message: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error processing your message. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in handle_text_message: {e}")
            await update.message.reply_text(
                "❌ An unexpected error occurred. Please try again."
            )
    
    async def handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages with captions."""
        try:
            message = update.message
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            
            # Check if this is part of a media group
            if message.media_group_id:
                # Add to media group collection
                photo = message.photo[-1]  # Get highest resolution
                processed_caption = None
                
                if message.caption:
                    processed_caption = self.link_replacer.process_text(message.caption)
                
                media_item = {
                    'type': 'photo',
                    'file_id': photo.file_id,
                    'caption': processed_caption if processed_caption != message.caption else message.caption,
                    'original_caption': message.caption
                }
                
                self.media_groups[message.media_group_id].append(media_item)
                logger.info(f"Added photo to media group {message.media_group_id}")
                
                # Wait a bit for more photos, then send as group
                await asyncio.sleep(1)
                
                # Check if we should send the group now
                if len(self.media_groups[message.media_group_id]) > 0:
                    await self.send_media_group(chat_id, message.media_group_id)
                
            else:
                # Single photo - handle normally
                original_caption = message.caption
                logger.info(f"Received single photo message from user {user_id}")
                
                if original_caption:
                    processed_caption = self.link_replacer.process_text(original_caption)
                    
                    if processed_caption != original_caption:
                        # Send photo with processed caption
                        photo = message.photo[-1]
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo.file_id,
                            caption=processed_caption
                        )
                        logger.info("Photo with processed caption sent back")
                    else:
                        # Send photo back as-is when no links found in caption
                        photo = message.photo[-1]
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo.file_id,
                            caption=original_caption
                        )
                else:
                    # Send photo back as-is when no caption
                    photo = message.photo[-1]
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo.file_id
                    )
        
        except TelegramError as e:
            logger.error(f"Telegram error in handle_photo_message: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error processing your photo. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in handle_photo_message: {e}")
            await update.message.reply_text(
                "❌ An unexpected error occurred while processing your photo."
            )
    
    async def send_media_group(self, chat_id: int, media_group_id: str):
        """Send collected media as a group."""
        try:
            if media_group_id not in self.media_groups:
                return
            
            media_items = self.media_groups[media_group_id]
            if not media_items:
                return
            
            # Create InputMedia objects
            media_group = []
            for i, item in enumerate(media_items):
                if item['type'] == 'photo':
                    # Only first item gets caption
                    caption = item['caption'] if i == 0 else None
                    media_group.append(InputMediaPhoto(
                        media=item['file_id'],
                        caption=caption
                    ))
                elif item['type'] == 'video':
                    caption = item['caption'] if i == 0 else None
                    media_group.append(InputMediaVideo(
                        media=item['file_id'],
                        caption=caption
                    ))
                elif item['type'] == 'document':
                    caption = item['caption'] if i == 0 else None
                    media_group.append(InputMediaDocument(
                        media=item['file_id'],
                        caption=caption
                    ))
                elif item['type'] == 'audio':
                    caption = item['caption'] if i == 0 else None
                    media_group.append(InputMediaAudio(
                        media=item['file_id'],
                        caption=caption
                    ))
                elif item['type'] == 'animation':
                    caption = item['caption'] if i == 0 else None
                    media_group.append(InputMediaAnimation(
                        media=item['file_id'],
                        caption=caption
                    ))
            
            if media_group:
                await self.application.bot.send_media_group(
                    chat_id=chat_id,
                    media=media_group
                )
                logger.info(f"Sent media group with {len(media_group)} items")
            
            # Clean up
            del self.media_groups[media_group_id]
            
        except Exception as e:
            logger.error(f"Error sending media group: {e}")
            # Clean up on error
            if media_group_id in self.media_groups:
                del self.media_groups[media_group_id]
    
    async def handle_video_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages with captions."""
        try:
            message = update.message
            original_caption = message.caption
            logger.info(f"Received video message from user {update.effective_user.id}")
            
            if original_caption:
                processed_caption = self.link_replacer.process_text(original_caption)
                
                if processed_caption != original_caption:
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=message.video.file_id,
                        caption=processed_caption
                    )
                    logger.info("Video with processed caption sent back")
                else:
                    # Send video back as-is when no links found in caption
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=message.video.file_id,
                        caption=original_caption
                    )
            else:
                # Send video back as-is when no caption
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=message.video.file_id
                )
        
        except TelegramError as e:
            logger.error(f"Telegram error in handle_video_message: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error processing your video. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in handle_video_message: {e}")
            await update.message.reply_text(
                "❌ An unexpected error occurred while processing your video."
            )
    
    async def handle_document_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document messages with captions."""
        try:
            message = update.message
            original_caption = message.caption
            logger.info(f"Received document message from user {update.effective_user.id}")
            
            if original_caption:
                processed_caption = self.link_replacer.process_text(original_caption)
                
                if processed_caption != original_caption:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=message.document.file_id,
                        caption=processed_caption
                    )
                    logger.info("Document with processed caption sent back")
                else:
                    # Send document back as-is when no links found in caption
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=message.document.file_id,
                        caption=original_caption
                    )
            else:
                # Send document back as-is when no caption
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=message.document.file_id
                )
        
        except TelegramError as e:
            logger.error(f"Telegram error in handle_document_message: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error processing your document. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in handle_document_message: {e}")
            await update.message.reply_text(
                "❌ An unexpected error occurred while processing your document."
            )
    
    async def handle_audio_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio messages with captions."""
        try:
            message = update.message
            original_caption = message.caption
            logger.info(f"Received audio message from user {update.effective_user.id}")
            
            if original_caption:
                processed_caption = self.link_replacer.process_text(original_caption)
                
                if processed_caption != original_caption:
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=message.audio.file_id,
                        caption=processed_caption
                    )
                    logger.info("Audio with processed caption sent back")
                else:
                    # Send audio back as-is when no links found in caption
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=message.audio.file_id,
                        caption=original_caption
                    )
            else:
                # Send audio back as-is when no caption
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=message.audio.file_id
                )
        
        except TelegramError as e:
            logger.error(f"Telegram error in handle_audio_message: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error processing your audio. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in handle_audio_message: {e}")
            await update.message.reply_text(
                "❌ An unexpected error occurred while processing your audio."
            )
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages."""
        await update.message.reply_text(
            "🎤 Voice messages don't contain text links to replace."
        )
        logger.info(f"Received voice message from user {update.effective_user.id}")
    
    async def handle_video_note_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video note messages."""
        await update.message.reply_text(
            "📹 Video notes don't contain text links to replace."
        )
        logger.info(f"Received video note from user {update.effective_user.id}")
    
    async def handle_sticker_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle sticker messages."""
        await update.message.reply_text(
            "😄 Stickers don't contain text links to replace."
        )
        logger.info(f"Received sticker from user {update.effective_user.id}")
    
    async def handle_animation_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle animation/GIF messages with captions."""
        try:
            message = update.message
            original_caption = message.caption
            logger.info(f"Received animation message from user {update.effective_user.id}")
            
            if original_caption:
                processed_caption = self.link_replacer.process_text(original_caption)
                
                if processed_caption != original_caption:
                    await context.bot.send_animation(
                        chat_id=update.effective_chat.id,
                        animation=message.animation.file_id,
                        caption=processed_caption
                    )
                    logger.info("Animation with processed caption sent back")
                else:
                    # Send animation back as-is when no links found in caption
                    await context.bot.send_animation(
                        chat_id=update.effective_chat.id,
                        animation=message.animation.file_id,
                        caption=original_caption
                    )
            else:
                # Send animation back as-is when no caption
                await context.bot.send_animation(
                    chat_id=update.effective_chat.id,
                    animation=message.animation.file_id
                )
        
        except TelegramError as e:
            logger.error(f"Telegram error in handle_animation_message: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error processing your animation. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in handle_animation_message: {e}")
            await update.message.reply_text(
                "❌ An unexpected error occurred while processing your animation."
            )
    
    async def start_bot(self):
        """Start the bot with polling."""
        logger.info("Starting Telegram Link Swap Bot...")
        logger.info(f"Bot token: {BOT_TOKEN[:10]}...")
        logger.info(f"Replacement link: {REPLACEMENT_LINK}")
        
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Bot is running! Press Ctrl+C to stop.")
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
        finally:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
    
    def run(self):
        """Run the bot."""
        try:
            asyncio.run(self.start_bot())
        except KeyboardInterrupt:
            logger.info("Bot stopped")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
