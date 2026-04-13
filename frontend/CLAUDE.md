# Frontend — Next.js 15 / TypeScript

## Stack
Next.js 15 (App Router), React 19, TypeScript, pnpm, TailwindCSS, @tanstack/react-query, Zustand

## Commands
- Install: `pnpm install`
- Dev server: `pnpm dev`
- Lint: `pnpm lint`
- Type check: `pnpm type-check`
- Build: `pnpm build`

## UI Layout
3-panel layout: Left sidebar (document manager) | Center (chat) | Right (source of truth panel)

## Architecture Rules
- Pages live in src/app/ (Next.js App Router file convention)
- API calls go through src/services/ — no fetch() calls inside components
- Server state (documents, messages) managed with @tanstack/react-query via src/hooks/
- Client UI state (right panel open/closed, selected chunk) managed with Zustand in src/store/
- Shared TypeScript types in src/types/ — reuse before defining new ones

## Do Not
- No direct fetch() in components — use service functions
- No inline styles — TailwindCSS classes only
- No `any` types — fix the type, don't suppress it
