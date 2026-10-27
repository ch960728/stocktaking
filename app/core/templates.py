import time

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

# Cache-busting query string for /static/* references, e.g. /static/css/style.css?v=...
# Browsers (and especially mobile in-app webviews) cache static assets aggressively;
# without this, a CSS/JS edit can silently keep showing the old file on a phone that
# already visited the site. Changes on every server restart, which is simplest given
# this project has no asset build step to hash file contents.
templates.env.globals["asset_version"] = str(int(time.time()))
