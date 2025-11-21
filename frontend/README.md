# 🎨 LeetCode Team Dashboard - Modern Frontend

Beautiful, modern React + TypeScript frontend for the LeetCode Team Dashboard.

## ✨ Features

- 🔐 **JWT Authentication** - Secure login/register
- 📊 **Real-time Dashboard** - Team stats, leaderboard, podium
- 📈 **Analytics** - Trends, week-over-week changes, activity heatmap
- 👥 **Team Management** - Add/remove members
- 🎨 **Modern UI** - Glass morphism, gradients, smooth animations
- 📱 **Responsive** - Works on mobile, tablet, desktop
- ⚡ **Fast** - Vite build, React Query caching
- 🎭 **Animated** - Framer Motion transitions

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (20 recommended)
- npm or yarn
- Backend API running on port 8080

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at: **http://localhost:5173**

### Build for Production

```bash
npm run build
npm run preview  # Preview production build
```

## 📦 Tech Stack

### Core
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite 5** - Build tool
- **React Router 6** - Navigation

### UI & Styling
- **Tailwind CSS 3.4** - Utility-first CSS
- **shadcn/ui** - Beautiful component library
- **Framer Motion** - Animations
- **Lucide React** - Icons

### Data & State
- **TanStack Query (React Query v5)** - Server state management
- **Zustand** - Client state (auth)
- **Axios** - HTTP client

### Forms & Validation
- **React Hook Form** - Form management
- **Zod** - Schema validation

### Charts
- **Recharts** - Data visualization

### Utils
- **date-fns** - Date formatting
- **clsx** + **tailwind-merge** - Class name utilities

## 🏗️ Project Structure

```
frontend/
├── public/                # Static assets
├── src/
│   ├── components/        # React components
│   │   ├── ui/           # shadcn/ui base components
│   │   ├── dashboard/    # Dashboard-specific components
│   │   ├── charts/       # Chart components
│   │   ├── layout/       # Layout components
│   │   └── modals/       # Modal components
│   ├── pages/            # Page components
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Analytics.tsx
│   │   └── Team.tsx
│   ├── services/         # API clients
│   │   └── api.ts        # Axios instance + API methods
│   ├── hooks/            # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useTeam.ts
│   │   └── useAnalytics.ts
│   ├── stores/           # Zustand stores
│   │   └── authStore.ts  # Auth state
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   ├── utils/            # Utility functions
│   │   ├── cn.ts         # Class name merger
│   │   └── format.ts     # Formatters
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## 🎨 Design System

### Color Palette (Dark Mode)
```css
Background:   #0F172A (slate-900)
Card:         Frosted glass with backdrop-blur
Primary:      #8B5CF6 (purple-500)
Secondary:    #06B6D4 (cyan-500)
Success:      #10B981 (emerald-500)
Warning:      #F59E0B (amber-500)
Error:        #EF4444 (red-500)
Text Primary: #F1F5F9 (slate-100)
Text Secondary: #94A3B8 (slate-400)
```

### Typography
- Font Family: Inter (modern sans-serif)
- Headings: 600-700 weight
- Body: 400 weight
- Code: Fira Code

### Spacing
- Base unit: 4px (0.25rem)
- Container max-width: 1400px
- Padding: 2rem

## 🔌 API Integration

### Base URL
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
```

### Endpoints Used

#### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register
- `GET /api/auth/me` - Get current user

#### Team Management
- `GET /api/team/members` - Get all members
- `POST /api/team/members` - Add member
- `DELETE /api/team/members/{username}` - Remove member
- `GET /api/team/stats` - Get team stats

#### Analytics
- `GET /api/analytics/history` - Get history
- `POST /api/analytics/snapshot` - Record snapshot
- `GET /api/analytics/trends?weeks=12` - Get trends
- `GET /api/analytics/week-over-week` - Get changes

### Authentication Flow

```typescript
// 1. Login
const { access_token } = await authApi.login({ username, password });

// 2. Store token
localStorage.setItem('access_token', access_token);
useAuthStore.getState().setToken(access_token);

// 3. Fetch user profile
const user = await authApi.getCurrentUser();
useAuthStore.getState().setUser(user);

// 4. All subsequent requests include:
// Authorization: Bearer <token>
```

## 🧪 Environment Variables

Create `.env` file:

```bash
# API base URL
VITE_API_URL=http://localhost:8080

# Optional: Analytics
VITE_ENABLE_ANALYTICS=false
```

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t leetcode-frontend .
```

### Run Container

```bash
docker run -p 3000:3000 \
  -e VITE_API_URL=http://localhost:8080 \
  leetcode-frontend
```

### Docker Compose

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8080
    depends_on:
      - api
```

## 📱 Features Breakdown

### Dashboard Page
- Team overview stats (4 cards)
- Top 3 podium display
- Full team leaderboard (sortable)
- Quick action buttons
- Recent activity indicator

### Analytics Page
- Trend charts (last 12 weeks)
- Week-over-week comparison table
- Difficulty breakdown pie charts
- Activity heatmap (GitHub-style)
- Export data button

### Team Page
- Member list with avatars
- Add member modal
- Remove member confirmation
- Real-time LeetCode stats
- Sorting & filtering

### Profile Page
- User information
- Team membership
- Personal stats
- Settings

## 🎭 Animations

### Page Transitions
- Fade in on mount
- Slide up effect
- Smooth exit animations

### Component Animations
- Hover scale (1.05x)
- Glow shadow on hover
- Number count-up
- Loading skeletons
- Toast slide-in

## 🔧 Development

### Available Scripts

```bash
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

### Code Style
- ESLint + TypeScript
- Prettier (recommended)
- Strict mode enabled
- No unused variables/imports

## 🎯 Performance

- Lazy loading for pages
- React Query caching (5 min for members)
- Code splitting
- Image optimization
- Tree shaking

## 📦 Bundle Size (Estimated)

- Initial: ~150 KB (gzipped)
- Total: ~300 KB (gzipped)
- Load time: < 2s on 3G

## 🚀 Deployment Checklist

- [ ] Environment variables set
- [ ] API URL configured
- [ ] Build successful (`npm run build`)
- [ ] No TypeScript errors
- [ ] No console errors
- [ ] Tested on Chrome, Firefox, Safari
- [ ] Responsive on mobile
- [ ] Dark mode working
- [ ] All animations smooth
- [ ] Performance > 90 (Lighthouse)

## 🆘 Troubleshooting

### API Connection Issues
1. Check API is running: `curl http://localhost:8080/api/health`
2. Verify CORS settings in backend
3. Check `VITE_API_URL` in `.env`

### Build Errors
1. Clear cache: `rm -rf node_modules .vite`
2. Reinstall: `npm install`
3. Rebuild: `npm run build`

### Authentication Issues
1. Clear localStorage: `localStorage.clear()`
2. Check JWT token format
3. Verify backend SECRET_KEY

## 📚 Documentation

- [API Documentation](../backend/README.md)
- [Design System](./DESIGN_SYSTEM.md)
- [Component Library](./COMPONENTS.md)

## 🎉 What's Next?

After setup:
1. Login with: `leetcodescamp` / `changeme123`
2. View your team dashboard
3. Add/remove members
4. Record weekly snapshots
5. Analyze trends

## 📄 License

MIT License - See backend LICENSE file

---

**Built with ❤️ using React + TypeScript + Vite**
