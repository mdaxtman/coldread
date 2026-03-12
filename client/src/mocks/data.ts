// Hardcoded mock data for frontend development.
// Mimics a realistic pipeline result for a Senior Frontend Engineer role.

import type { FitReport, JobDescription, ResumeVariant } from '../types'
import type { PipelineResult } from '../hooks/usePipelineResult'

export const MOCK_JOB_DESCRIPTION: JobDescription = {
  id: 'mock-jd-001',
  userId: 'mock-user-001',
  title: 'Senior Frontend Engineer',
  company: 'TechCorp',
  content: `Senior Frontend Engineer — TechCorp

We're looking for an experienced React developer to join our platform team. You'll build and maintain our component library, optimize runtime performance, and help shape our client-side data layer architecture.

Requirements:
• 5+ years with React and TypeScript in production
• Experience building and maintaining a component library
• Strong understanding of client-side data layer patterns (e.g. GraphQL, TanStack Query)
• GraphQL API experience (Apollo Client preferred)
• Familiarity with deployment pipeline tooling (CI/CD, GitHub Actions)
• Track record of runtime performance tuning and Core Web Vitals optimization
• Experience with mobile-first development and accessibility (WCAG 2.1)
• AWS infrastructure experience (CloudFront, S3, Lambda@Edge)

Nice to have:
• Micro-frontend architecture experience
• React Native development
• Peer review process leadership
• Agile/Scrum methodology`,
  createdAt: '2026-03-09T14:00:00Z',
}

export const MOCK_FIT_REPORT: FitReport = {
  id: 'mock-fit-001',
  userId: 'mock-user-001',
  jobDescriptionId: 'mock-jd-001',
  fitLevel: 'strong',
  matches: [
    'React and TypeScript (5+ years production experience)',
    'Component architecture and design system development',
    'REST API integration and state management',
    'Performance optimization and Core Web Vitals',
    'CI/CD pipelines with GitHub Actions',
    'Mentoring junior developers and code review',
    'Responsive design and accessibility (WCAG 2.1)',
    'Agile/Scrum workflow experience',
  ],
  gaps: [
    {
      requirement: 'GraphQL API experience',
      type: 'hard',
      notes:
        'Have REST expertise; GraphQL concepts are transferable. Could ramp up quickly with Apollo Client.',
    },
    {
      requirement: 'AWS infrastructure (CloudFront, S3, Lambda@Edge)',
      type: 'hard',
      notes: 'Familiar with Vercel/Netlify deployment. AWS-specific services would need learning.',
    },
    {
      requirement: 'Micro-frontend architecture',
      type: 'soft',
      notes:
        'Experience with monorepo setups and module federation concepts, but not a dedicated micro-frontend deployment.',
    },
    {
      requirement: 'Native mobile development (React Native)',
      type: 'soft',
      notes: 'Web-only background. React Native shares mental models but would be a new platform.',
    },
  ],
  terminology: [
    { myTerm: 'state management', jdTerm: 'client-side data layer' },
    { myTerm: 'design system', jdTerm: 'component library' },
    { myTerm: 'CI/CD', jdTerm: 'deployment pipeline' },
    { myTerm: 'code review', jdTerm: 'peer review process' },
    { myTerm: 'responsive design', jdTerm: 'mobile-first development' },
    { myTerm: 'performance optimization', jdTerm: 'runtime performance tuning' },
  ],
  reasoning:
    'Strong fit overall. The candidate has deep React/TypeScript expertise that directly maps to the core requirements. Component architecture and design system experience are standout strengths. The primary gaps are in GraphQL (which is learnable given REST proficiency) and AWS-specific infrastructure. The soft gaps around micro-frontends and React Native are listed as "nice to have" in the JD and don\'t affect the core fit assessment. Terminology differences are cosmetic — the underlying skills align well.',
  createdAt: '2026-03-09T14:30:00Z',
}

export const MOCK_RESUME_VARIANT: ResumeVariant = {
  id: 'mock-variant-001',
  userId: 'mock-user-001',
  jobDescriptionId: 'mock-jd-001',
  content: `ALEX MORGAN
Senior Frontend Engineer

SUMMARY
Frontend engineer with 6+ years building production React applications. Specialized in component library development, client-side data layer architecture, and runtime performance tuning. Track record of leading mobile-first development initiatives and establishing peer review processes that improved code quality across teams.

EXPERIENCE

Senior Frontend Engineer — Acme Corp (2022–Present)
• Architected and maintained a shared component library serving 12 product teams, reducing UI inconsistencies by 60%
• Led migration from class components to hooks-based architecture, improving bundle size by 25%
• Implemented client-side data layer using TanStack Query, reducing API calls by 40% through intelligent caching
• Established deployment pipeline with GitHub Actions: lint, test, build, preview deploys on every PR
• Mentored 3 junior engineers through structured peer review process and pair programming sessions

Frontend Engineer — StartupXYZ (2020–2022)
• Built the customer-facing dashboard from scratch using React, TypeScript, and Vite
• Achieved 95+ Lighthouse scores through runtime performance tuning (code splitting, lazy loading, image optimization)
• Developed mobile-first responsive layouts serving 50K+ monthly active users
• Integrated REST APIs with custom hooks and centralized error handling

Frontend Developer — WebAgency Co (2018–2020)
• Delivered 15+ client projects using React, Next.js, and CSS Modules
• Built reusable form components with accessibility compliance (WCAG 2.1 AA)
• Collaborated in Agile/Scrum teams with 2-week sprint cycles

SKILLS
Languages: TypeScript, JavaScript (ES2024), HTML5, CSS3
Frameworks: React 18, Next.js 14, Vite, TanStack Router
Styling: CSS Modules, Tailwind CSS, Styled Components
State: TanStack Query, Zustand, React Context
Testing: Vitest, React Testing Library, Playwright
Tools: Git, GitHub Actions, Figma, VS Code
`,
  version: 1,
  parentVariantId: null,
  screenerReport: {
    keywordCoverage: {
      React: true,
      TypeScript: true,
      'component library': true,
      GraphQL: false,
      'REST API': true,
      'CI/CD': true,
      'performance optimization': true,
      AWS: false,
      'responsive design': true,
      accessibility: true,
      'micro-frontend': false,
      'React Native': false,
      'state management': true,
      'code review': true,
      Agile: true,
    },
    semanticScore: 0.82,
    terminologyMismatches: [
      { myTerm: 'state management', jdTerm: 'client-side data layer' },
      { myTerm: 'design system', jdTerm: 'component library' },
    ],
    overallScore: 0.78,
  },
  createdAt: '2026-03-09T14:31:00Z',
}

export const MOCK_PIPELINE_RESULT: PipelineResult = {
  jobDescription: MOCK_JOB_DESCRIPTION,
  fitReport: MOCK_FIT_REPORT,
  resumeVariant: MOCK_RESUME_VARIANT,
}
