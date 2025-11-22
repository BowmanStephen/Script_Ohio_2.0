# Vercel Deployment Guide

Complete guide for deploying the React + Vite web app to Vercel via GitHub.

## Prerequisites

- Vercel account (free tier is sufficient)
- GitHub repository with the code
- Node.js 18+ (automatically provided by Vercel)

## Deployment Steps

### 1. Connect Repository to Vercel

1. Log in to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
   - Select your repository from the list
   - Click **"Import"**

### 2. Configure Project Settings

In the project configuration screen:

1. **Framework Preset**: Vercel should auto-detect "Vite"
   - If not, select **"Vite"** from the dropdown

2. **Root Directory**: Set to `web_app`
   - Click **"Edit"** next to Root Directory
   - Enter: `web_app`
   - This tells Vercel the app is in a subdirectory

3. **Build and Output Settings** (should auto-populate from `vercel.json`):
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
   - **Development Command**: `npm run dev`

4. **Environment Variables**: 
   - None required for this app
   - All data is static JSON files bundled with the app

5. Click **"Deploy"**

### 3. Wait for Deployment

- Vercel will install dependencies, build the app, and deploy
- First deployment typically takes 1-2 minutes
- You'll see a live URL when deployment completes

### 4. Verify Deployment

After deployment succeeds:

1. **Check the deployment URL**:
   - Vercel provides: `https://your-project-name.vercel.app`
   - Click the URL to open your deployed app

2. **Verify app loads correctly**:
   - Page should load without errors
   - CSS/styles should be applied
   - JavaScript should be functional
   - Week 13 game data should display

3. **Test core functionality**:
   - Model selection works
   - Feature weight sliders work
   - Training simulation runs
   - All views (Predictions, WCFL Strategy, etc.) load

## Automatic Deployments

Once connected, Vercel automatically deploys:

### Production Deployments
- **Trigger**: Every push to `main` branch
- **URL**: `https://your-project-name.vercel.app`
- **Status**: Production environment

### Preview Deployments
- **Trigger**: Every pull request and push to other branches
- **URL**: `https://your-project-name-git-branch-username.vercel.app`
- **Status**: Preview environment (identical to production, different URL)

## Configuration Files

### `vercel.json`
Located in `web_app/vercel.json`:

- **Build settings**: Build command, output directory, framework
- **Headers**: Cache control for static assets, security headers
- **Rewrites**: SPA routing fallback to `index.html`

### `package.json`
Located in `web_app/package.json`:

- **Build script**: `"build": "vite build"`
- **Dependencies**: All React, Vite, and UI libraries

## Custom Domain (Optional)

To use your own domain:

1. Go to **Project Settings** → **Domains**
2. Click **"Add Domain"**
3. Enter your domain (e.g., `app.yourdomain.com`)
4. Follow DNS configuration instructions
5. Vercel provides SSL certificates automatically

## Environment Variables (If Needed Later)

If you need to add environment variables later:

1. Go to **Project Settings** → **Environment Variables**
2. Add variables for:
   - **Production**: Production deployments only
   - **Preview**: Preview deployments only
   - **Development**: Local development only
3. Redeploy after adding variables

## Troubleshooting

### Build Fails

**Issue**: Build fails during deployment

**Solutions**:
1. Check build logs in Vercel dashboard for errors
2. Verify `web_app/package.json` has all dependencies
3. Test build locally: `cd web_app && npm run build`
4. Ensure Node.js version is compatible (Vercel uses 18+)

### Assets Not Loading

**Issue**: CSS/JS files return 404

**Solutions**:
1. Verify `vercel.json` output directory is `dist`
2. Check that build completes successfully
3. Ensure `dist/` directory exists after build
4. Check browser console for specific 404 errors

### App Shows Blank Page

**Issue**: Deployed app shows blank page

**Solutions**:
1. Check browser console for JavaScript errors
2. Verify `index.html` is in `dist/` output
3. Check that rewrites in `vercel.json` are correct
4. Ensure all imports use relative paths or proper aliases

### Root Directory Issues

**Issue**: Vercel can't find the app

**Solutions**:
1. Verify Root Directory is set to `web_app` (not `/web_app`)
2. Ensure `vercel.json` is in `web_app/` directory
3. Check that `package.json` exists in `web_app/`

## Monitoring

### Deployment Logs
- View logs in Vercel dashboard for each deployment
- Real-time build output available during deployment

### Analytics (Optional)
- Enable Vercel Analytics in Project Settings
- Free tier includes basic analytics

### Performance Monitoring
- Vercel automatically monitors deployment performance
- Check "Deployments" tab for metrics

## Rollback

To rollback to a previous deployment:

1. Go to **Deployments** tab in Vercel dashboard
2. Find the deployment you want to restore
3. Click the **"..."** menu → **"Promote to Production"**
4. Confirms and your site will use that deployment

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vite Deployment Guide](https://vite.dev/guide/static-deploy.html#vercel)
- [Vercel CLI](https://vercel.com/docs/cli) (for local testing)

## Support

If you encounter issues:
1. Check Vercel deployment logs
2. Test build locally: `cd web_app && npm run build`
3. Verify all configuration files are correct
4. Review Vercel documentation for framework-specific issues

