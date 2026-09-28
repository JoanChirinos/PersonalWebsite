# PersonalWebsite

Landing page and app directory for `app.joanchirinos.com`, served by nginx on the home MacBook.

Static only — Svelte 5 + Vite + TypeScript + Tailwind v4 + daisyUI, compiled to plain files. No backend.

## Adding an app to the directory

Add an entry to `APPS` in `src/apps.ts`. That's the whole change.

## Serving static files

Anything in `public/` is copied to the site root at build time, so `public/foo.pdf` is served at `/foo.pdf`.

## Local development

```
npm install
npm run dev
```

## Deploying

Pushing to `main` triggers the self-hosted runner on the MacBook, which runs `deploy.sh`.
To deploy by hand:

```
ssh macbook.joanchirinos.com '~/PersonalWebsite/deploy.sh'
```

`deploy.sh` builds into `dist/`, then publishes to `live/` only after a clean build, so a
failed build leaves the running site untouched. nginx serves `live/` via a symlink at
`/opt/homebrew/var/www/home`.

## History

This repo previously held a Flask version of Avalon Notes Helper (1.0). It's preserved
in git history at the `v1-flask` tag:

```
git checkout v1-flask
```
