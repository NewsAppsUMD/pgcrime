# Deployment Guide

This document explains how to deploy the Prince George's County Crime Statistics Dashboard to GitHub Pages.

## GitHub Pages Deployment

### Initial Setup

1. **Enable GitHub Pages**:
   - Go to your repository on GitHub
   - Click **Settings** → **Pages**
   - Under "Source", select **GitHub Actions**
   - Click **Save**

2. **Verify Workflow File**:
   The repository includes `.github/workflows/deploy-pages.yml` which handles automatic deployment.

### How It Works

The deployment workflow:
- Triggers on every push to `main` branch that affects:
  - `docs/**` files
  - `data/json/**` files
  - The workflow file itself
- Can also be manually triggered from the Actions tab
- Copies docs files and data to GitHub Pages
- Creates necessary symlinks for data access

### Manual Deployment

To manually trigger a deployment:

1. Go to the **Actions** tab in your GitHub repository
2. Click on **Deploy to GitHub Pages** workflow
3. Click **Run workflow** button
4. Select the `main` branch
5. Click **Run workflow**

### Deployment Status

Check deployment status:
- Go to **Actions** tab
- View the latest "Deploy to GitHub Pages" workflow run
- Green checkmark ✓ = successful deployment
- Red X ✗ = failed deployment (click for details)

### Accessing Your Site

Once deployed, your site will be available at:
```
https://newsappsumd.github.io/pgcrime/
```

**Note**: First deployment may take 5-10 minutes. Subsequent deployments are faster.

### Troubleshooting

#### Deployment Fails

1. **Check workflow logs**:
   - Go to Actions tab
   - Click on the failed workflow run
   - Expand each step to see error messages

2. **Common issues**:
   - Missing `data/json/` files
   - Invalid JSON format
   - Permissions not set correctly

#### Site Shows 404

1. **Verify GitHub Pages settings**:
   - Settings → Pages
   - Source should be "GitHub Actions"

2. **Check deployment status**:
   - Actions tab should show successful deployment
   - Look for green checkmark

#### Data Not Loading

1. **Check browser console** for errors:
   - Right-click → Inspect → Console tab
   - Look for 404 errors or CORS issues

2. **Verify data path**:
   - Data files should be at `./data/json/YYYYMMDD.json`
   - Check that symlink was created in build step

## Automatic Daily Updates

The repository also includes a workflow (`.github/workflows/daily-crime-report.yml`) that:
- Runs daily at 9 AM ET
- Downloads the latest crime report
- Parses it to JSON
- Commits new data to the repository
- Automatically triggers docs deployment

This means your dashboard updates automatically every day with new crime data!

## Custom Domain (Optional)

To use a custom domain like `crime.yourdomain.com`:

1. **Add CNAME record** in your DNS settings:
   ```
   crime.yourdomain.com → newsappsumd.github.io
   ```

2. **Configure in GitHub**:
   - Settings → Pages
   - Custom domain: Enter `crime.yourdomain.com`
   - Click Save
   - Wait for DNS check to complete

3. **Enable HTTPS**:
   - Check "Enforce HTTPS" once DNS propagates

## Alternative Hosting Platforms

### Netlify

1. Connect your GitHub repository
2. Build settings:
   - Build command: (leave empty)
   - Publish directory: `docs`
3. Deploy

### Vercel

1. Import your GitHub repository
2. Framework preset: Other
3. Root directory: `docs`
4. Deploy

## Local Testing

Before pushing to production, test locally:

```bash
cd docs
python -m http.server 8000
```

Open http://localhost:8000 to preview changes.

## Rollback

To rollback to a previous version:

1. Go to Actions tab
2. Find the successful deployment you want to restore
3. Click "Re-run all jobs"

Or revert via git:
```bash
git revert <commit-hash>
git push origin main
```

## Monitoring

Monitor your deployment:
- **Uptime**: Use services like UptimeRobot
- **Analytics**: Add Google Analytics or similar
- **Errors**: Check browser console on deployed site

## Security Notes

- All data is public (Prince George's County crime reports)
- No authentication required
- No sensitive data stored
- HTTPS enforced by GitHub Pages
- No server-side code or database

## Support

If you encounter issues:
1. Check the workflow logs in Actions tab
2. Review this deployment guide
3. Check GitHub Pages documentation
4. Verify JSON data format

## Maintenance

Regular tasks:
- Monitor daily workflow runs
- Check that data is updating correctly
- Review any failed workflow runs
- Update dependencies periodically (Chart.js CDN)
