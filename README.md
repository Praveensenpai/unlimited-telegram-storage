# Unlimited Telegram Storage (Beta)

*Note: This is a beta release. The tool will be marked as stable once all features are complete and thoroughly tested.*

## 🚀 Overview

Unlimited Telegram Storage allows you to store files of **unlimited size** by splitting them into chunks smaller than 2GB and uploading them to a dedicated Telegram storage chat. It provides a seamless way to upload, download, manage, and sync your stored files with an efficient command-line interface and beautiful progress displays.

## ✨ Features

- **Unlimited File Size**: Supports any file size by splitting it into manageable chunks.
- **Seamless Upload & Download**: Automatically chunks large files during upload and merges them back during download.
- **Metadata Management**: Keeps track of uploaded files and their respective chunks.
- **Sync Mechanism**: Ensures local metadata and Telegram storage remain synchronized.
- **Efficient CLI Interface**: Offers an easy-to-use command-line tool.
- **Rich Progress Display**: Shows detailed progress bars for uploads and downloads.

## 🛠 Installation

### Install `uv`

#### On macOS and Linux:
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### On Windows:
```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install Dependencies
```sh
uv sync
```

## 🎮 Usage

### 1️⃣ Initialize the Configuration
```sh
uv run cli.py init
```
- Prompts for **API ID, API Hash, and Phone Number**.
- Creates a new Telegram session.

### 2️⃣ Set Up Storage Chat
```sh
uv run cli.py setup-storage-chat
```
- Create a **new private Telegram channel** (make sure you are the admin, of course, you are if you created it lol).
- Use `@userinfobot` to get the **group ID** of the channel.
- Prompts for **Storage Chat ID**.
- Verifies admin permissions.

### 3️⃣ Sync Metadata
```sh
uv run cli.py sync
```
- Ensures local and Telegram metadata are synchronized.

### 4️⃣ Upload a File
```sh
uv run cli.py upload /path/to/large_file.zip
```
- Splits the file into **chunks** if larger than 2GB.
- Uploads each chunk to Telegram.
- Stores metadata for easy retrieval.

### 5️⃣ List Uploaded Files
```sh
uv run cli.py list-files
```
- Displays all uploaded files stored in Telegram.

### 6️⃣ Download a File
```sh
uv run cli.py download FILE_ID /path/to/save/
```
- Fetches all chunks from Telegram.
- Merges them back into the original file.

### 7️⃣ Delete a File
```sh
uv run cli.py delete FILE_ID
```
- Removes the file from Telegram.
- Updates metadata accordingly.

### 8️⃣ Delete All Files
```sh
uv run cli.py delete-all
```
- Deletes **all** files stored in Telegram.
- Clears local metadata.

## 🌌 Complete Example Workflow

```sh
# Step 1: Initialize Telegram session
uv run cli.py init

# Step 2: Setup storage chat
uv run cli.py setup-storage-chat

# Step 3: Sync metadata
uv run cli.py sync

# Step 4: Upload a file
uv run cli.py upload movie.mkv

# Step 5: List all uploaded files
uv run cli.py list-files

# Step 6: Download a file
uv run cli.py download 123abc /downloads/

# Step 7: Delete a file
uv run cli.py delete 123abc

# Step 8: Delete all files (if needed)
uv run cli.py delete-all
```

## 🔮 Future Plans

- **Encryption**: Securely encrypt files before uploading to ensure privacy.
- **Better Metadata Handling**: Improve tracking and retrieval of stored files.
- **Other**: Give me idea.


## 💜 License

MIT License. Contributions are welcome!
