import * as Sentry from "@sentry/nextjs";

export function initSentry() {
  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

  if (dsn) {
    Sentry.init({
      dsn,
      tracesSampleRate: 0.1, // 10% of transactions
      environment: process.env.NODE_ENV,
      // Ignore certain errors
      ignoreErrors: [
        // Random plugins/extensions
        "top.GLOBALS",
        // See: http://blog.errorception.com/2012/03/tale-of-unfindable-js-error.html
        "originalCreateNotification",
        "canvas.contentDocument",
        "MyApp_RemoveAllHighlights",
        // https://github.com/getsentry/sentry-javascript/issues/289
        "chrome-extension://",
        "moz-extension://",
      ],
    });
  }
}
