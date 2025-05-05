import re
import os
import sys
import time
from typing import Optional
from colorama import init, Fore, Style
from backend.app.pipeline.transcript_to_vectordb import transcript_to_vectordb_pipeline
from backend.app.pipeline.url_to_transcript import log_url

# Initialize colorama for cross-platform colored terminal text
init(autoreset=True)

def validate_video_url(url: str) -> bool:
    """
    Validates if the provided URL is a supported video URL (YouTube or Instagram).
    Returns True if valid, False otherwise.
    """
    # YouTube patterns (standard, shorts, and youtu.be)
    youtube_patterns = [
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=)[\w-]{11}(\S*)?$',
        r'^(https?://)?(www\.)?(youtube\.com/shorts/)[\w-]{11}(\S*)?$',
        r'^(https?://)?(youtu\.be/)[\w-]{11}(\S*)?$'
    ]
    
    # Instagram patterns (posts and reels)
    instagram_patterns = [
        r'^(https?://)?(www\.)?(instagram\.com/p/)[\w-]{11}(/)?(\S*)?$',
        r'^(https?://)?(www\.)?(instagram\.com/reel/)[\w-]{11}(/)?(\S*)?$'
    ]
    
    # Check YouTube patterns
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    # Check Instagram patterns
    for pattern in instagram_patterns:
        if re.match(pattern, url):
            return True
    
    return False

def get_video_url_from_user() -> Optional[str]:
    """
    Interactive terminal UI for getting a video URL from the user.
    Supports YouTube and Instagram videos.
    Returns the validated URL or None if the user cancels.
    """
    # Clear terminal screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Display header
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'Video to Vector DB Pipeline':^60}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
    
    # Show description
    print(f"{Fore.WHITE}This tool will process a YouTube or Instagram video through the following steps:")
    print(f"{Fore.GREEN}1. {Fore.WHITE}Download and transcribe the video")
    print(f"{Fore.GREEN}2. {Fore.WHITE}Chunk the transcript into processable blocks")
    print(f"{Fore.GREEN}3. {Fore.WHITE}Tag and analyze the content")
    print(f"{Fore.GREEN}4. {Fore.WHITE}Generate embeddings")
    print(f"{Fore.GREEN}5. {Fore.WHITE}Store in vector database for future queries\n")
    
    # URL input with validation
    print(f"{Fore.YELLOW}{Style.BRIGHT}Enter a YouTube or Instagram URL {Style.RESET_ALL}{Fore.YELLOW}(or type 'exit' to cancel):{Style.RESET_ALL}")
    
    while True:
        try:
            url = input(f"{Fore.WHITE}> {Style.RESET_ALL}").strip()
            
            if url.lower() in ['exit', 'quit', 'q', 'cancel']:
                print(f"\n{Fore.RED}Operation cancelled by user.{Style.RESET_ALL}")
                return None
            
            # URL validation
            if validate_video_url(url):
                # URL looks valid
                print(f"\n{Fore.GREEN}URL accepted! {Style.RESET_ALL}")
                
                # Identify platform
                platform = "YouTube" if "youtube" in url or "youtu.be" in url else "Instagram"
                print(f"{Fore.WHITE}Detected platform: {Fore.CYAN}{platform}{Style.RESET_ALL}")
                
                # Confirm processing animation
                print(f"{Fore.WHITE}Preparing to process", end="")
                for _ in range(3):
                    time.sleep(0.3)
                    print(f"{Fore.WHITE}.", end="", flush=True)
                print("\n")
                
                return url
            else:
                print(f"{Fore.RED}Invalid video URL format. Please enter a valid YouTube or Instagram URL.{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Examples:")
                print(f"{Fore.WHITE}- YouTube: https://www.youtube.com/watch?v=d")
                print(f"{Fore.WHITE}- YouTube Shorts: https://www.youtube.com/shorts/Y")
                print(f"{Fore.WHITE}- Instagram Post: https://www.instagram.com/p/D")
                print(f"{Fore.WHITE}- Instagram Reel: https://www.instagram.com/reel/D/{Style.RESET_ALL}\n")
        
        except KeyboardInterrupt:
            print(f"\n\n{Fore.RED}Operation cancelled by user.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"\n{Fore.RED}An error occurred: {str(e)}{Style.RESET_ALL}")

def run_pipeline_interactive():
    """
    Run the YouTube to VectorDB pipeline with an interactive UI.
    """
    try:
        
        url = get_video_url_from_user()
        
        if url:
            print(f"{Fore.CYAN}Starting pipeline with URL: {Style.RESET_ALL}{url}\n")
            
            transcript_url = log_url(url)

            if not transcript_url:
                print(f"\n{Fore.RED}{Style.BRIGHT}Pipeline failed. Please check the logs above for details.{Style.RESET_ALL}")
            
            # Add transcription verification warning
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️ IMPORTANT: {Style.RESET_ALL}{Fore.YELLOW}Automatic transcription may not be accurate.")
            print(f"{Fore.YELLOW}It's strongly recommended that you review your transcription before continuing.")
            print(f"{Fore.YELLOW}Inaccurate transcriptions will lead to poor vector embeddings, search results and would be slop for our model.")
            
            # Ask for confirmation
            print(f"\n{Fore.WHITE}Do you want to continue anyway? (y/n){Style.RESET_ALL}")
            confirmation = input(f"{Fore.WHITE}> {Style.RESET_ALL}").strip().lower()
            
            if confirmation not in ['y', 'Y','yes']:
                print(f"\n{Fore.GREEN}{Style.BRIGHT} Good Call!  Feel free to change your .txt under speaker_transcript folder file to match the actual audio {Style.RESET_ALL}")
                print(f"\n{Fore.GREEN}{Style.BRIGHT}Just reuse the url after you've made sure everything is fine and we'll pickup from here! {Style.RESET_ALL}")
                return
        

            print(f"{Fore.WHITE}Oh well, Here we go...", end="")
            # Run the actual pipeline
            success = transcript_to_vectordb_pipeline(transcript_url)
            
            if success:
                print(f"\n{Fore.GREEN}{Style.BRIGHT}Pipeline completed successfully!{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}{Style.BRIGHT}Pipeline failed. Please check the logs above for details.{Style.RESET_ALL}")
            
            # Ask if user wants to process another video
            print(f"\n{Fore.YELLOW}Would you like to process another video? (y/n){Style.RESET_ALL}")
            choice = input(f"{Fore.WHITE}> {Style.RESET_ALL}").strip().lower()
            
            if choice in ['y', 'yes']:
                # Recursive call to process another video
                run_pipeline_interactive()
            else:
                print(f"\n{Fore.CYAN}Thank you for using the YouTube to Vector DB Pipeline!{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}Operation cancelled by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}An unexpected error occurred: {str(e)}{Style.RESET_ALL}")

# Example usage
if __name__ == "__main__":
    run_pipeline_interactive()