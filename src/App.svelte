<script lang="ts">
  import { APPS } from './apps';
  import { Moon, Sun, ArrowUpRight } from '@lucide/svelte';

  let isDark = $state(
    localStorage.getItem('theme')
      ? localStorage.getItem('theme') === 'dark'
      : matchMedia('(prefers-color-scheme: dark)').matches
  );

  $effect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });
</script>

<div class="min-h-screen bg-base-200">
  <div class="mx-auto w-full max-w-3xl px-4 py-10">
    <div class="mb-8 flex items-start justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold tracking-tight">Joan's Stuff</h1>
        <p class="mt-2 text-base-content/60">
          A directory of things I've built. Mostly for my friends, occasionally for me.
        </p>
      </div>
      <label class="swap swap-rotate btn btn-ghost btn-circle shrink-0" aria-label="Toggle dark mode">
        <input type="checkbox" bind:checked={isDark} />
        <span class="swap-on"><Moon size={18} /></span>
        <span class="swap-off"><Sun size={18} /></span>
      </label>
    </div>

    <h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-base-content/50">Apps</h2>
    <ul class="space-y-3">
      {#each APPS as app (app.href)}
        <li>
          <a href={app.href} class="card bg-base-100 shadow-sm transition hover:shadow-md">
            <div class="card-body flex-row items-center gap-4 p-4">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-semibold">{app.name}</span>
                  {#if app.tag}
                    <span class="badge badge-primary badge-sm">{app.tag}</span>
                  {/if}
                </div>
                <p class="mt-1 text-sm text-base-content/60">{app.description}</p>
              </div>
              <ArrowUpRight size={18} class="shrink-0 text-base-content/40" />
            </div>
          </a>
        </li>
      {/each}
    </ul>

    <footer class="mt-10 text-xs text-base-content/40">
      <a class="link link-hover" href="https://github.com/JoanChirinos">github.com/JoanChirinos</a>
    </footer>
  </div>
</div>
