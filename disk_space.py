import os
import time
import psutil
import pathlib
import heapq
import anthropic

# Set your Anthropic API Key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # Ensure API key is set in environment variables
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Function to check disk space
def check_disk_space(threshold_percentage=10):
    disk_usage = psutil.disk_usage("/")
    free_percentage = disk_usage.free / disk_usage.total * 100
    return free_percentage, disk_usage

# Function to find the largest files in a directory
def find_large_files(directory="/", size_threshold_mb=500, max_files=5):
    large_files = []
    try:
        directory_path = pathlib.Path(directory)
        for file in directory_path.rglob("*"):
            if file.is_file():
                size_mb = file.stat().st_size / (1024 ** 2)
                if size_mb >= size_threshold_mb:
                    heapq.heappush(large_files, (-size_mb, file))
                    if len(large_files) > max_files:
                        heapq.heappop(large_files)
    except PermissionError:
        pass  # Skip files without access permissions
    return [(-size, path) for size, path in large_files]

# Function to generate alert using Claude-3 Sonnet
def generate_alert(disk_usage, large_files):
    large_files_text = "\n".join(
        [f"{size:.2f} MB - {path}" for size, path in large_files]
    )
    prompt = (
        f"The current disk usage is {disk_usage.percent}%, and only {disk_usage.free / (1024**3):.2f} GB remains free.\n"
        f"I found the following large files on your system:\n{large_files_text}\n"
        "Write a playful and quirky alert message nudging the user to clean up these files if they are not in use."
    )
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error generating alert: {str(e)}"

# Main function to monitor disk space
def monitor_disk_space(threshold_percentage=60, check_interval=60):
    print(f"Monitoring disk space... Alert threshold set at {threshold_percentage}% free space.")
    while True:
        free_percentage, disk_usage = check_disk_space(threshold_percentage)
        if free_percentage < threshold_percentage:
            print("\n[ALERT] Low disk space detected!")
            large_files = find_large_files("/", size_threshold_mb=500, max_files=5)
            alert_message = generate_alert(disk_usage, large_files)
            print(alert_message)
        else:
            print(f"Disk space is sufficient: {free_percentage:.2f}% free.")
        time.sleep(check_interval)

# Run the script
if __name__ == "__main__":
    threshold = 60  # Alert threshold set to 10% free space
    check_interval = 60  # Check every 5 minutes
    monitor_disk_space(threshold, check_interval)
