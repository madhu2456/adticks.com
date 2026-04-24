'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import {
  ChevronDown, Zap, Bell, Settings, LogOut, Check,
  Plus, Globe, User, Loader2, Search, Command, Moon, Sun,
  TrendingUp, AlertTriangle, RefreshCw, ArrowUpRight,
  Calendar, ChevronRight,
} from 'lucide-react'
import { useTheme } from 'next-themes'
import { cn } from '@/lib/utils'
import { formatRelativeTime } from '@/lib/utils'
import { api } from '@/lib/api'
import { clearTokens, getUser } from '@/lib/auth'
import { useProjects, useActiveProject } from '@/hooks/useProject'
import { useAlertModal } from '@/hooks/useAlertModal'
import { ProjectModal } from '@/components/projects/ProjectModal'
import { ScanModal } from '@/components/layout/ScanModal'
import { CommandPalette } from '@/components/layout/CommandPalette'
import { Project, User as UserType } from '@/lib/types'

/* ── Data ─────────────────────────────────────────────────────────────── */
const NOTIFICATIONS: any[] = []

/* ── Hooks ────────────────────────────────────────────────────────────── */
function useOutsideClick(ref: React.RefObject<HTMLElement>, cb: () => void) {
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) cb()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [ref, cb])
}

/* ── Dropdown shell ───────────────────────────────────────────────────── */
function Dropdown({ open, children, className }: { open: boolean; children: React.ReactNode; className?: string }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0, y: 6, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 4, scale: 0.97 }}
          transition={{ duration: 0.14, ease: [0.4, 0, 0.2, 1] }}
          className={cn('absolute top-full mt-2 z-50 rounded-xl overflow-hidden', className)}
          style={{
            background: 'rgba(14,14,16,0.98)',
            backdropFilter: 'blur(24px)',
            WebkitBackdropFilter: 'blur(24px)',
            border: '1px solid rgba(255,255,255,0.08)',
            boxShadow: '0 8px 40px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.04)',
          }}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

/* ── Props ────────────────────────────────────────────────────────────── */
interface HeaderProps {
  sidebarCollapsed: boolean
  currentPage?: string
}

/* ── Component ────────────────────────────────────────────────────────── */
function Header({ sidebarCollapsed, currentPage = 'Overview' }: HeaderProps) {
  const router = useRouter()
  const { data: projectList = [] } = useProjects()
  const { activeProject, setActiveId } = useActiveProject()
  
  const [projectOpen,      setProjectOpen]      = useState(false)
  const [notifOpen,        setNotifOpen]        = useState(false)
  const [userOpen,         setUserOpen]         = useState(false)
  const [isScanModalOpen,  setScanModalOpen]    = useState(false)
  const [isModalOpen,      setModalOpen]        = useState(false)
  const [isCommandOpen,    setCommandOpen]      = useState(false)
  
  const [notifications, setNotifications] = useState(NOTIFICATIONS)
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme } = useTheme()
  const { showAlert, AlertModal } = useAlertModal()
  const [user, setUser] = useState<{ name: string; email: string; initials: string; plan?: string; avatarUrl?: string } | null>(null)

  const projectRef = useRef<HTMLDivElement>(null!)
  const notifRef   = useRef<HTMLDivElement>(null!)
  const userRef    = useRef<HTMLDivElement>(null!)

  useOutsideClick(projectRef, () => setProjectOpen(false))
  useOutsideClick(notifRef,   () => setNotifOpen(false))
  useOutsideClick(userRef,    () => setUserOpen(false))

  const closeAll = () => { setProjectOpen(false); setNotifOpen(false); setUserOpen(false) }

  const unreadCount = notifications.filter(n => !n.read).length

  const activeProjectData = activeProject || { 
    id: '0', 
    name: 'No Project', 
    domain: 'Add a project', 
    color: '#64748b', 
    initials: '?',
    brand_name: 'No Project'
  }

  const handleScan = () => {
    if (!activeProject) return
    setScanModalOpen(true)
  }

  const markAllRead = () => setNotifications(prev => prev.map(n => ({ ...n, read: true })))

  const handleLogout = async () => {
    try {
      await api.auth.logout()
    } catch (err) {
      console.error('Logout failed:', err)
    } finally {
      clearTokens()
      router.push('/login')
    }
  }

  useEffect(() => {
    setMounted(true)
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

  // ⌘K trigger
  const handleCommandPalette = useCallback(() => {
    setCommandOpen(true)
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        handleCommandPalette()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleCommandPalette])

  return (
    <>
      <header
        className="fixed top-0 right-0 z-30 flex items-center h-14 gap-2"
        style={{
          left: sidebarCollapsed ? 60 : 224,
          paddingLeft: '16px',
          paddingRight: '16px',
          transition: 'left 0.22s cubic-bezier(0.4,0,0.2,1)',
          background: 'var(--glass)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid var(--border)',
        }}
      >
      {/* ── Scan progress bar ────────────────────────────────────────── */}
      {/* Removed - now handled by ScanModal */}

      {/* ── Left: Project selector ───────────────────────────────────── */}
      <div ref={projectRef} className="relative">
        <button
          onClick={() => { closeAll(); setProjectOpen(p => !p) }}
          className="flex items-center gap-2 h-8 px-2.5 rounded-lg transition-all hover:bg-white/[0.05] group"
          style={{ border: '1px solid rgba(255,255,255,0.07)' }}
        >
          {/* Project color dot */}
          <div
            className="w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 text-[9px] font-bold text-white"
            style={{
              background: `linear-gradient(135deg, ${activeProjectData.color || '#6366f1'}, ${activeProjectData.color || '#6366f1'}cc)`,
              boxShadow: `0 0 8px ${activeProjectData.color || '#6366f1'}40`,
            }}
          >
            {activeProjectData.initials || (activeProjectData.brand_name || activeProjectData.name || "?")[0].toUpperCase()}
          </div>
          <div className="text-left hidden sm:block">
            <p className="text-[13px] font-semibold text-text-1 leading-none">{activeProjectData.brand_name || activeProjectData.name}</p>
            <p className="text-[10px] text-text-3 mt-0.5 leading-none flex items-center gap-1">
              <Globe size={9} />
              {activeProjectData.domain}
            </p>
          </div>
          <ChevronDown
            size={12}
            className={cn('text-text-3 transition-transform flex-shrink-0', projectOpen && 'rotate-180')}
          />
        </button>

        <Dropdown open={projectOpen} className="left-0 w-64">
          <div className="px-2 pt-2 pb-1 max-h-[60vh] overflow-y-auto">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 px-1.5 pb-1.5">Switch Project</p>
            {projectList.length === 0 ? (
              <p className="text-[11px] text-text-3 px-2 py-4 text-center italic">No projects found.</p>
            ) : (
              projectList.map(project => (
                <button
                  key={project.id}
                  onClick={() => { setActiveId(project.id); setProjectOpen(false) }}
                  className="w-full flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-white/[0.05] transition-colors text-left group"
                >
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-[11px] font-bold text-white"
                    style={{ background: `linear-gradient(135deg, ${project.color || '#6366f1'}, ${project.color || '#6366f1'}cc)` }}
                  >
                    {project.initials || (project.brand_name || project.name || "?")[0].toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium text-text-1 truncate">{project.brand_name || project.name}</p>
                    <p className="text-[11px] text-text-3 truncate">{project.domain}</p>
                  </div>
                  {project.id === activeProject?.id && (
                    <Check size={13} className="text-primary flex-shrink-0" />
                  )}
                </button>
              ))
            )}
          </div>
          <div className="p-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <button 
              onClick={() => { setModalOpen(true); setProjectOpen(false) }}
              className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/[0.05] transition-colors text-text-3 hover:text-text-2"
            >
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ border: '1px dashed rgba(255,255,255,0.12)' }}
              >
                <Plus size={12} />
              </div>
              <span className="text-[13px] font-medium">Add new project</span>
            </button>
          </div>
        </Dropdown>
      </div>

      {/* ── Breadcrumb ───────────────────────────────────────────────── */}
      <div className="hidden md:flex items-center gap-1 text-[13px] text-text-3 ml-1">
        <ChevronRight size={13} />
        <span className="text-text-2 font-medium">{currentPage}</span>
      </div>

      {/* ── Command palette shortcut ─────────────────────────────────── */}
      <button
        onClick={handleCommandPalette}
        className="hidden lg:flex items-center gap-2 ml-2 h-8 px-3 rounded-lg text-text-3 hover:text-text-2 hover:bg-white/[0.04] transition-all"
        style={{ border: '1px solid rgba(255,255,255,0.06)' }}
      >
        <Search size={13} />
        <span className="text-[12px]">Search anything...</span>
        <div className="flex items-center gap-0.5 ml-2">
          <kbd style={{ fontSize: '10px' }}>⌘</kbd>
          <kbd style={{ fontSize: '10px' }}>K</kbd>
        </div>
      </button>

      {/* ── Spacer ───────────────────────────────────────────────────── */}
      <div className="flex-1" />

      {/* ── Right actions ────────────────────────────────────────────── */}
      <div className="flex items-center gap-1.5">

        {/* Theme toggle */}
        {mounted && (
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="flex items-center justify-center w-8 h-8 rounded-lg text-text-3 hover:text-text-2 hover:bg-white/[0.05] transition-all"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        )}

        {/* Live indicator */}
        <div className="hidden sm:flex items-center gap-1.5 h-7 px-2.5 rounded-lg text-[11px] font-medium text-success"
          style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.15)' }}
        >
          <span className="live-dot" />
          <span>Live</span>
        </div>

        {/* Run Full Scan */}
        <button
          onClick={handleScan}
          disabled={!activeProject}
          title={!activeProject ? "Select a project to run scan" : "Run AI Scan"}
          className={cn(
            'flex items-center gap-1.5 h-8 px-3 rounded-lg text-[13px] font-semibold text-white transition-all',
            'disabled:opacity-40 disabled:cursor-not-allowed',
          )}
          style={{
            background: 'linear-gradient(135deg, #6366f1, #7c3aed)',
            boxShadow: '0 0 12px rgba(99,102,241,0.25), 0 2px 8px rgba(0,0,0,0.3)',
          }}
        >
          <Zap size={13} />
          <span className="hidden sm:inline">Run Scan</span>
        </button>

        {/* Notification bell */}
        <div ref={notifRef} className="relative">
          <button
            onClick={() => { closeAll(); setNotifOpen(p => !p) }}
            className="relative flex items-center justify-center w-8 h-8 rounded-lg text-text-3 hover:text-text-2 hover:bg-white/[0.05] transition-all"
          >
            <Bell size={15} />
            {unreadCount > 0 && (
              <span
                className="absolute top-1 right-1 flex items-center justify-center w-3.5 h-3.5 rounded-full bg-danger text-[8px] font-bold text-white"
                style={{ boxShadow: '0 0 6px rgba(239,68,68,0.5)' }}
              >
                {unreadCount}
              </span>
            )}
          </button>

          <Dropdown open={notifOpen} className="right-0 w-[340px]">
            <div
              className="flex items-center justify-between px-3 py-2.5"
              style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="flex items-center gap-2">
                <p className="text-[13px] font-semibold text-text-1">Notifications</p>
                {unreadCount > 0 && (
                  <span className="h-5 px-1.5 rounded-full bg-danger/15 text-danger text-[10px] font-bold flex items-center">
                    {unreadCount} new
                  </span>
                )}
              </div>
              {unreadCount > 0 && (
                <button onClick={markAllRead} className="text-[11px] text-primary hover:text-primary/80 transition-colors">
                  Mark all read
                </button>
              )}
            </div>
            <div className="max-h-80 overflow-y-auto custom-scroll">
              {notifications.map((notif) => {
                const Icon = notif.icon
                return (
                  <div
                    key={notif.id}
                    className={cn(
                      'flex gap-3 px-3 py-3 hover:bg-white/[0.03] transition-colors cursor-pointer',
                      !notif.read && 'bg-primary/[0.04]',
                    )}
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ background: `${notif.accent}15`, border: `1px solid ${notif.accent}20` }}
                    >
                      <Icon size={14} style={{ color: notif.accent }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p className={cn('text-[13px] font-medium leading-snug', notif.read ? 'text-text-2' : 'text-text-1')}>
                          {notif.title}
                        </p>
                        {!notif.read && (
                          <span
                            className="mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0"
                            style={{ background: notif.accent }}
                          />
                        )}
                      </div>
                      <p className="text-[11px] text-text-3 mt-0.5">{notif.body}</p>
                      <p className="text-[10px] text-text-3 mt-1">{formatRelativeTime(notif.time)}</p>
                    </div>
                  </div>
                )
              })}
            </div>
            <div
              className="px-3 py-2"
              style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
            >
            <button 
              onClick={() => { 
                showAlert({
                  title: "Coming Soon",
                  message: "Notifications inbox coming soon!",
                  type: "info",
                  confirmText: "Got it",
                });
                closeAll(); 
              }}
              className="flex items-center gap-1 text-[11px] text-text-3 hover:text-text-2 transition-colors"
            >
              View all notifications <ArrowUpRight size={11} />
            </button>
            </div>
          </Dropdown>
        </div>

        {/* User avatar ─────────────────────────────────────────────── */}
        <div ref={userRef} className="relative">
          <button
            onClick={() => { closeAll(); setUserOpen(p => !p) }}
            className="flex items-center justify-center w-8 h-8 rounded-full text-white text-[11px] font-bold hover:opacity-90 transition-all overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              boxShadow: '0 0 0 2px rgba(99,102,241,0.25)',
            }}
          >
            {user?.avatarUrl ? (
              <img src={user.avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
            ) : (
              user?.initials || '??'
            )}
          </button>

          <Dropdown open={userOpen} className="right-0 w-56">
            <div
              className="px-3 py-2.5"
              style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="flex items-center gap-2.5">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0 overflow-hidden"
                  style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
                >
                  {user?.avatarUrl ? (
                    <img src={user.avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                  ) : (
                    user?.initials || '??'
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <p className="text-[13px] font-semibold text-text-1 truncate">{user?.name || 'Loading...'}</p>
                    {user?.plan && user.plan !== 'free' && (
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-primary/20 text-primary uppercase tracking-wider">
                        {user.plan}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-text-3 truncate">{user?.email || '...'}</p>
                </div>
              </div>
            </div>
            <div className="p-1.5">
              {[
                { icon: User,     label: 'Profile',         href: '/settings?tab=profile' },
                { icon: Settings, label: 'Settings',        href: '/settings' },
                { icon: Calendar, label: 'Usage & Billing', href: '/settings?tab=plan' },
              ].map(({ icon: Icon, label, href }) => (
                <button
                  key={label}
                  onClick={() => { router.push(href); closeAll(); }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-white/[0.05] transition-colors text-text-2 hover:text-text-1 text-[13px] font-medium"
                >
                  <Icon size={13} className="text-text-3" />
                  {label}
                </button>
              ))}
            </div>
            <div className="p-1.5" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
              <button 
                onClick={handleLogout}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-danger/10 transition-colors text-text-2 hover:text-danger text-[13px] font-medium"
              >
                <LogOut size={13} />
                Sign out
              </button>
            </div>
          </Dropdown>
        </div>
      </div>
      </header>

      <ProjectModal 
        isOpen={isModalOpen} 
        onClose={() => setModalOpen(false)} 
        onSuccess={(id) => setActiveId(id)}
      />

      <ScanModal 
        isOpen={isScanModalOpen} 
        onClose={() => setScanModalOpen(false)} 
        projectId={activeProject?.id}
      />

      <CommandPalette 
        isOpen={isCommandOpen} 
        onClose={() => setCommandOpen(false)} 
      />

      {AlertModal}
    </>
  )
}

export default Header;
export { Header };
