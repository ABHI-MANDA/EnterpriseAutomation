import React from 'react';

export const metadata = {
  title: 'Real Estate Enterprise Operations Command Center',
  description: 'AI-Powered Centralized Real Estate Intelligence & Operations Dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, background: '#0b0f19', color: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
        {children}
      </body>
    </html>
  );
}
