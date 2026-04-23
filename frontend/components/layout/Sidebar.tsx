'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, Search, Sparkles, Activity, Megaphone, Zap,
  Settings, BarChart2, ChevronRight, ChevronLeft, ArrowRight,
  HelpCircle, ChevronsUpDown, User, Moon, ExternalLink, MapPin,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useEffect, useState } from 'react'
import { getUser } from '@/lib/auth'

/* ── Types ─────────────────────────────────────────────────────────── */
interface NavItem {
  label: string
  href: string
  icon: React.ElementType
  badge?: string | number
  badgeType?: 'count' | 'new' | 'alert'
  shortcut?: string
  description?: string
}

/* ── Nav sections ───────────────────────────────────────────────────── */
const NAV_SECTIONS = [
  {
    label: 'Main',
    items: [
      {
        label: 'Overview',
        href: '/',
        icon: LayoutDashboard,
        shortcut: 'G O',
        description: 'Brand visibility at a glance',
      },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      {
        label: 'SEO Hub',
        href: '/seo',
        icon: Search,
        shortcut: 'G S',
        description: 'Keywords & rank tracking',
      },
      {
        label: 'AEO Hub',
        href: '/aeo',
        icon: Sparkles,
        badge: 'BETA',
        badgeType: 'new' as const,
        shortcut: 'G A',
        description: 'LLM & AI visibility',
      },
      {
        label: 'Local SEO',
        href: '/geo',
        icon: MapPin,
        shortcut: 'G L',
        description: 'Maps & geo tracking',
      },
      {
        label: 'Search Console',
        href: '/gsc',
        icon: Activity,
        shortcut: 'G C',
        description: 'GSC impressions & CTR',
      },
    ],
  },
  {
    label: 'Performance',
    items: [
      {
        label: 'Ads',
        href: '/ads',
        icon: Megaphone,
        shortcut: 'G D',
        description: 'Campaign performance',
      },
      {
        label: 'Insights',
        href: '/insights',
        icon: Zap,
        shortcut: 'G I',
        description: 'AI-powered recommendations',
      },
    ],
  },
]

/* ── Badge component ─────────────────────────────────────────────────── */
function NavBadge({ badge, badgeType, collapsed }: { badge: string | number; badgeType?: string; collapsed?: boolean }) {
  if (collapsed) return null
  if (badgeType === 'new') {
    return (
      <span className="flex items-center gap-1 text-[9px] font-bold text-violet-400 bg-violet-500/12 px-1.5 py-0.5 rounded-full tracking-wide uppercase">
        <span className="relative flex h-1.5 w-1.5 flex-shrink-0">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-violet-400" />
        </span>
        NEW
      </span>
    )
  }
  if (badgeType === 'alert') {
    return (
      <span className="flex items-center justify-center h-4 min-w-[1rem] px-1 text-[10px] font-bold bg-danger/90 text-white rounded-full">
        {badge}
      </span>
    )
  }
  return (
    <span className="text-[10px] font-medium text-text-3 bg-surface-1 px-1.5 py-0.5 rounded-md tabular-nums">
      {badge}
    </span>
  )
}

/* ── Tooltip ─────────────────────────────────────────────────────────── */
function CollapsedTooltip({ item, visible }: { item: NavItem; visible: boolean }) {
  if (!visible) return null
  return (
    <div className="absolute left-full top-1/2 -translate-y-1/2 ml-3 z-50 pointer-events-none animate-fade-in">
      <div
        className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium text-text-1 whitespace-nowrap"
        style={{
          background: 'rgba(24,24,27,0.98)',
          border: '1px solid rgba(255,255,255,0.10)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
        }}
      >
        <span>{item.label}</span>
        {item.shortcut && (
          <kbd className="text-[9px] opacity-60">{item.shortcut}</kbd>
        )}
        {item.badge !== undefined && (
          <NavBadge badge={item.badge} badgeType={item.badgeType} />
        )}
      </div>
      <div
        className="absolute right-full top-1/2 -translate-y-1/2 border-[5px] border-transparent"
        style={{ borderRightColor: 'rgba(24,24,27,0.98)' }}
      />
    </div>
  )
}

/* ── Props ───────────────────────────────────────────────────────────── */
interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

/* ── Main component ──────────────────────────────────────────────────── */
function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [hoveredItem, setHoveredItem] = useState<string | null>(null)
  const [user, setUser] = useState<{ name: string; email: string; initials: string; plan?: string; avatarUrl?: string } | null>(null)

  useEffect(() => {
    const currentUser = getUser()
    if (currentUser) {
      const name = currentUser.full_name || currentUser.name || 'User'
      const initials = name
        ? name.split(' ').map(n => n[0]).join('').toUpperCase()
        : currentUser.email[0].toUpperCase()
      setUser({
        name,
        email: currentUser.email,
        initials,
        plan: currentUser.plan,
        avatarUrl: currentUser.avatar_url
      })
    }
  }, [])

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href)
  }

  return (
    <motion.aside
      animate={{ width: collapsed ? 60 : 224 }}
      transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
      className="fixed left-0 top-0 h-screen z-40 flex flex-col overflow-hidden"
      style={{
        background: 'var(--bg)',
        borderRight: '1px solid var(--border)',
      }}
    >
      {/* ── Logo ─────────────────────────────────────────────────────── */}
      <div
        className="relative flex items-center h-14 px-3.5 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.055)' }}
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div
            className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              boxShadow: '0 0 14px rgba(99,102,241,0.35)',
            }}
          >
            <BarChart2 className="w-4 h-4 text-white" strokeWidth={2.5} />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -6 }}
                transition={{ duration: 0.14 }}
                className="flex items-baseline gap-1.5 min-w-0"
              >
                <span className="gradient-text font-bold text-[15px] tracking-tight whitespace-nowrap">
                  AdTicks
                </span>
                <span
                  className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full whitespace-nowrap"
                  style={{
                    background: 'rgba(99,102,241,0.15)',
                    color: '#818cf8',
                    border: '1px solid rgba(99,102,241,0.2)',
                  }}
                >
                  BETA
                </span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full flex items-center justify-center z-50 hover:scale-110 transition-transform"
          style={{
            background: '#1a1a1e',
            border: '1px solid rgba(255,255,255,0.10)',
            boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
          }}
        >
          {collapsed
            ? <ChevronRight className="w-3 h-3 text-text-2" />
            : <ChevronLeft  className="w-3 h-3 text-text-2" />}
        </button>
      </div>

      {/* ── Nav ──────────────────────────────────────────────────────── */}
      <nav className="flex-1 py-3 overflow-y-auto overflow-x-hidden scrollbar-none">

        {NAV_SECTIONS.map((section, si) => (
          <div key={section.label} className={cn('px-2', si > 0 && 'mt-1')}>
            {/* Section label */}
            <AnimatePresence>
              {!collapsed && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="px-2 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-widest text-text-3"
                >
                  {section.label}
                </motion.p>
              )}
            </AnimatePresence>
            {collapsed && si > 0 && (
              <div className="h-px mx-1 mb-1.5 mt-2" style={{ background: 'rgba(255,255,255,0.05)' }} />
            )}

            {/* Items */}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = isActive(item.href)
                const Icon = item.icon
                const hovered = hoveredItem === item.href

                return (
                  <div
                    key={item.href}
                    className="relative"
                    onMouseEnter={() => setHoveredItem(item.href)}
                    onMouseLeave={() => setHoveredItem(null)}
                  >
                    <Link
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      className={cn(
                        'relative flex items-center gap-2.5 rounded-lg select-none overflow-hidden',
                        collapsed ? 'h-9 w-9 mx-auto justify-center' : 'h-8 px-2',
                        active
                          ? 'text-white'
                          : 'text-text-3 hover:text-text-1',
                      )}
                      style={
                        active
                          ? {
                              background: 'rgba(99,102,241,0.14)',
                              boxShadow: 'inset 0 0 0 1px rgba(99,102,241,0.2)',
                            }
                          : hovered
                          ? { background: 'rgba(255,255,255,0.04)' }
                          : {}
                      }
                    >
                      {/* Active indicator */}
                      {active && !collapsed && (
                        <span
                          className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 rounded-r-full"
                          style={{ background: '#6366f1' }}
                        />
                      )}

                      <Icon
                        className={cn(
                          'flex-shrink-0 transition-colors',
                          active ? 'text-primary' : 'text-text-3',
                        )}
                        size={15}
                        strokeWidth={active ? 2.5 : 2}
                      />

                      <AnimatePresence>
                        {!collapsed && (
                          <motion.span
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.12 }}
                            className={cn(
                              'text-[13px] font-medium whitespace-nowrap flex-1 min-w-0',
                              active ? 'text-text-1' : 'text-text-2',
                            )}
                          >
                            {item.label}
                          </motion.span>
                        )}
                      </AnimatePresence>

                      {/* Badge */}
                      <AnimatePresence>
                        {!collapsed && item.badge !== undefined && (
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                          >
                            <NavBadge badge={item.badge} badgeType={item.badgeType} />
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Keyboard shortcut on hover */}
                      <AnimatePresence>
                        {!collapsed && hovered && !active && item.shortcut && (
                          <motion.kbd
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="ml-auto"
                            style={{ fontSize: '9px' }}
                          >
                            {item.shortcut}
                          </motion.kbd>
                        )}
                      </AnimatePresence>
                    </Link>

                    {/* Collapsed tooltip */}
                    {collapsed && <CollapsedTooltip item={item} visible={hovered} />}
                  </div>
                )
              })}
            </div>
          </div>
        ))}

        {/* ── Settings / Help ─────────────────────────────────────────── */}
        <div
          className="px-2 mt-2 pt-2"
          style={{ borderTop: '1px solid rgba(255,255,255,0.055)' }}
        >
          {[
            { label: 'Settings', href: '/settings', icon: Settings, shortcut: 'G ,' },
            { label: 'Help & Docs', href: '/help', icon: HelpCircle, shortcut: '?' },
          ].map((item) => {
            const active = pathname === item.href
            const Icon = item.icon
            const hovered = hoveredItem === item.href

            return (
              <div
                key={item.href}
                className="relative"
                onMouseEnter={() => setHoveredItem(item.href)}
                onMouseLeave={() => setHoveredItem(null)}
              >
                <Link
                  href={item.href}
                  title={collapsed ? item.label : undefined}
                  className={cn(
                    'flex items-center gap-2.5 rounded-lg',
                    collapsed ? 'h-9 w-9 mx-auto justify-center' : 'h-8 px-2',
                    active ? 'text-text-1 bg-surface-3' : 'text-text-3 hover:text-text-2',
                  )}
                  style={hovered && !active ? { background: 'rgba(255,255,255,0.04)' } : {}}
                >
                  <Icon size={15} strokeWidth={2} className="flex-shrink-0" />
                  <AnimatePresence>
                    {!collapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="text-[13px] font-medium flex-1"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                  <AnimatePresence>
                    {!collapsed && hovered && item.shortcut && (
                      <motion.kbd
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="ml-auto"
                        style={{ fontSize: '9px' }}
                      >
                        {item.shortcut}
                      </motion.kbd>
                    )}
                  </AnimatePresence>
                </Link>
                {collapsed && <CollapsedTooltip item={item} visible={hovered} />}
              </div>
            )
          })}
        </div>
      </nav>

      {/* ── Trial / Upgrade banner ───────────────────────────────────── */}
      {user?.plan === 'free' && (
        <div className="flex-shrink-0" style={{ borderTop: '1px solid rgba(255,255,255,0.055)' }}>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 6 }}
                className="p-3"
              >
                <div
                  className="rounded-xl p-3 space-y-2.5 relative overflow-hidden"
                  style={{
                    background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06))',
                    border: '1px solid rgba(99,102,241,0.18)',
                  }}
                >
                  {/* Subtle glow orb */}
                  <div
                    className="absolute -top-4 -right-4 w-16 h-16 rounded-full pointer-events-none"
                    style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.2), transparent 70%)', filter: 'blur(12px)' }}
                  />
                  <div className="flex items-center justify-between relative">
                    <div>
                      <p className="text-[11px] font-semibold text-text-2">Trial Plan</p>
                      <p className="text-xs font-semibold text-warning mt-0.5">14 days remaining</p>
                    </div>
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center"
                      style={{ background: 'rgba(234,179,8,0.12)', border: '1px solid rgba(234,179,8,0.2)' }}
                    >
                      <Zap className="w-3.5 h-3.5 text-warning" />
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-1">
                    <div
                      className="h-1 rounded-full overflow-hidden relative"
                      style={{ background: 'rgba(255,255,255,0.06)' }}
                    >
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: '80%',
                          background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                          boxShadow: '0 0 6px rgba(99,102,241,0.5)',
                        }}
                      />
                    </div>
                    <p className="text-[10px] text-text-3">80% of trial period used</p>
                  </div>

                  <button
                    onClick={() => router.push('/settings?tab=plan')}
                    className="w-full flex items-center justify-center gap-1.5 h-7 rounded-lg text-[12px] font-semibold text-white transition-opacity hover:opacity-90"
                    style={{
                      background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                      boxShadow: '0 2px 8px rgba(99,102,241,0.3)',
                    }}
                  >
                    Upgrade to Pro
                    <ArrowRight size={11} />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Collapsed: just the zap icon */}
          {collapsed && (
            <div className="py-2 flex justify-center">
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center cursor-pointer transition-colors"
                style={{ background: 'rgba(234,179,8,0.10)' }}
                title="Upgrade to Pro"
              >
                <Zap className="w-4 h-4 text-warning" />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── User section ──────────────────────────────────────────── */}
      <div
        className={cn(
          'flex items-center gap-2.5 cursor-pointer hover:bg-white/[0.03] transition-colors',
          collapsed ? 'justify-center p-2.5' : 'px-3 py-2.5',
        )}
        style={{ borderTop: user?.plan !== 'free' ? '1px solid rgba(255,255,255,0.055)' : 'none' }}
      >
          <div
            className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[11px] font-bold text-white"
            style={{
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              boxShadow: '0 0 0 2px rgba(99,102,241,0.2)',
            }}
          >
            {user?.initials || '??'}
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 min-w-0"
              >
                <div className="flex items-center gap-1.5">
                  <p className="text-[12px] font-semibold text-text-1 truncate leading-none">{user?.name || 'Loading...'}</p>
                  {user?.plan && user.plan !== 'free' && (
                    <span className="text-[8px] font-bold px-1 py-0 rounded bg-primary/20 text-primary uppercase tracking-wider">
                      {user.plan}
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-text-3 truncate mt-0.5">{user?.email || '...'}</p>
              </motion.div>
            )}
          </AnimatePresence>
          <AnimatePresence>
            {!collapsed && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <ChevronsUpDown size={13} className="text-text-3 flex-shrink-0" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
    </motion.aside>
  )
}

export default Sidebar;
export { Sidebar };
