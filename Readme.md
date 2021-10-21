## GalaxyGallery

This is supposed to be the next generation Private Tracker.

## Requirements

Python 3.8+

```bash
pip install -r requirements.txt
```

## Usage

Configure your database URL and website information in `config.yml` file.

Make sure you have initialized your database indicated by the files in `scripts` folder.

If you want to use the SMTP client to send emails, run the following command before your lanuch the server.

```bash
export SMTP_PASSWORD=password_for_your_email
```

Run development server with the following commands:

```bash
uvicorn main:gg --reload --host 0.0.0.0
```