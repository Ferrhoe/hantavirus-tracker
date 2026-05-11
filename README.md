# MV Hondius Hantavirus Tracker

Automated tracking of hantavirus spread from the MV Hondius cruise ship outbreak, with automatic news monitoring and hourly updates via GitHub Actions.

## Features

✅ **Automatic Updates** - GitHub Actions monitors news feeds every hour  
✅ **Live Dashboard** - Real-time world map, timeline chart, and case counts  
✅ **Zero Cost** - Runs entirely on free GitHub services  
✅ **No Manual Updates** - News monitoring is fully automated  
✅ **Shareable Link** - Deploy to GitHub Pages for public access  

## Repository Structure

```
hantavirus-tracker/
├── index.html                    # Main tracker dashboard
├── data/
│   └── tracker-data.json        # Data file (updated hourly by GitHub Actions)
├── scripts/
│   └── monitor_news.py          # News monitoring script
└── .github/
    └── workflows/
        └── update-data.yml      # GitHub Actions workflow
```

## Setup Instructions

### 1. Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Create a new repository: `hantavirus-tracker`
3. Choose **Public** (required for GitHub Pages)
4. Click "Create repository"

### 2. Add Files to Repository

Clone your new repo locally:
```bash
git clone https://github.com/YOUR_USERNAME/hantavirus-tracker.git
cd hantavirus-tracker
```

Create the directory structure:
```bash
mkdir -p data scripts .github/workflows
```

Add the files:

**`index.html`** - Copy the main tracker HTML file

**`data/tracker-data.json`** - Copy the JSON data file

**`scripts/monitor_news.py`** - Copy the news monitoring script

**`.github/workflows/update-data.yml`** - Copy the GitHub Actions workflow

### 3. Push to GitHub

```bash
git add .
git commit -m "Initial commit: hantavirus tracker setup"
git push origin main
```

### 4. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Source", select:
   - Branch: `main`
   - Folder: `/ (root)`
4. Click **Save**
5. Wait 1-2 minutes, then your site will be live at:
   ```
   https://YOUR_USERNAME.github.io/hantavirus-tracker/
   ```

### 5. Verify GitHub Actions is Running

1. Go to your repository
2. Click **Actions** tab
3. You should see "Update Hantavirus Data" workflow
4. The next run will occur at the top of the next hour (or manually trigger it)

To manually trigger an update:
1. Click the workflow name "Update Hantavirus Data"
2. Click **Run workflow** → **Run workflow**

## How It Works

### Data Flow

```
GitHub Actions (Hourly)
    ↓
Scripts/monitor_news.py (Fetches news)
    ↓
Parse articles for case numbers
    ↓
Update data/tracker-data.json
    ↓
Push changes to GitHub
    ↓
Website loads new data (auto-refreshes every 5 min)
```

### News Sources Monitored

The monitoring script checks:
- **News feeds**: Bloomberg, Reuters, BBC, CNBC
- **Health feeds**: WHO, CDC

The script looks for:
- Keywords: "hantavirus", "hondius", "andes virus"
- Case numbers: "X confirmed cases", "X deaths"
- Automatically updates if new counts are found

## Customization

### Add More News Sources

Edit `scripts/monitor_news.py`, add to `NEWS_SOURCES` list:

```python
NEWS_SOURCES = [
    'https://feeds.your-news-site.com/rss',
    # ... add more URLs
]
```

### Change Update Frequency

Edit `.github/workflows/update-data.yml`, change the cron schedule:

```yaml
schedule:
  - cron: '0 */2 * * *'  # Every 2 hours
  - cron: '0 0,12 * * *' # Noon and midnight
```

[Cron syntax guide](https://crontab.guru/)

### Manually Update Data

Edit `data/tracker-data.json` directly in GitHub's web editor:
1. Click the file
2. Click the pencil icon
3. Make changes
4. Click "Commit changes"

## Monitoring & Troubleshooting

### Check if GitHub Actions is Working

1. Go to **Actions** tab
2. Look for "Update Hantavirus Data" workflow
3. Check if it ran successfully (green checkmark)
4. Click on a run to see detailed logs

### Common Issues

**Issue**: Workflow shows error  
**Solution**: Check the workflow logs for details. Most common: Python package not found - ensure `pip install` commands are correct.

**Issue**: Data not updating on website  
**Solution**: 
- Hard refresh your browser: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)
- Check that `data/tracker-data.json` was actually committed and pushed
- Verify GitHub Pages is enabled and showing the right branch

**Issue**: News not being detected  
**Solution**: 
- Check workflow logs in Actions tab
- Verify news sources are still publishing RSS feeds
- Manually add news to `tracker-data.json` temporarily

## Testing Locally

To test the news monitoring script locally:

```bash
# Install dependencies
pip install requests beautifulsoup4 feedparser

# Run the script
python scripts/monitor_news.py

# Check the output
cat data/tracker-data.json
```

## Deployment Alternatives

### GitHub Pages (Recommended)
- ✅ Free
- ✅ Auto-updates from GitHub
- ✅ No additional setup
- Built into GitHub

### Vercel
- Go to [vercel.com](https://vercel.com)
- Import your GitHub repository
- Click Deploy
- Gets your own domain like `hantavirus-tracker.vercel.app`

### Netlify
- Go to [netlify.com](https://netlify.com)
- Click "New site from Git"
- Connect GitHub and select repository
- Deploy automatically

## Security Notes

- Repository is public (required for GitHub Pages)
- No sensitive data is stored
- GitHub Actions runs with minimal permissions (read/write to repo only)
- All news sources are publicly available

## Contributing

To improve the tracker:

1. Fork the repository
2. Create a feature branch
3. Make improvements
4. Submit a pull request

Possible improvements:
- Add more news sources
- Better number extraction from articles
- Regional/state-level tracking
- Contact tracing visualization
- Predictive modeling

## FAQ

**Q: How often does data update?**  
A: Every hour on the hour. GitHub Actions runs at 0:00, 1:00, 2:00, etc. UTC.

**Q: Can I track other outbreaks?**  
A: Yes! Modify the search keywords in `scripts/monitor_news.py` and update the country tracking in `data/tracker-data.json`.

**Q: What if an article updates case numbers incorrectly?**  
A: The script uses regex pattern matching and can miss context. You can always manually correct the JSON file on GitHub.

**Q: Will this work forever?**  
A: GitHub Actions and GitHub Pages have no storage/compute limits for public projects. This will work indefinitely as long as GitHub offers the service.

**Q: Can I export the data?**  
A: Yes! The data is just JSON. You can:
- Download it directly from GitHub
- Use the GitHub API to fetch it programmatically
- Import into Excel/spreadsheets

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review GitHub Actions logs
3. Check that all files are in the correct locations
4. Verify GitHub Pages settings

---

**Last Updated**: May 2026  
**Status**: Active (Last auto-update check)
