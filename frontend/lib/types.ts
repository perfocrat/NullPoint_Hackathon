export type Skill = {
  name: string;
  status: "signal" | "observed" | "unverified" | string;
  evidence: string;
};

export type SkillGap = {
  priority: string;
  name: string;
  description: string;
  action: string;
};

export type RoleFit = {
  name: string;
  fit: number;
  primary: boolean;
  description: string;
};

export type RoadmapStep = {
  phase: string;
  duration: string;
  title: string;
  description: string;
  task: string;
};

export type CareerAnalysis = {
  score: number;
  targetRole: string;
  scoreStatus?: string;
  explanation?: string;
  breakdown?: {
    skillMatch?: number;
    projectEvidence?: number;
    projectQuality?: number;
    activity?: number;
    roleRequirements?: number;
  };
  skills: Skill[];
  gaps: SkillGap[];
  roles: RoleFit[];
  roadmap: RoadmapStep[];
  sources?: {
    githubUser: string;
    githubProfileName: string | null;
    githubAccountCreatedAt: string | null;
    githubPublicRepoCount: number | null;
    githubFollowers: number | null;
    repositoriesReviewed: number;
    originalRepositories: number;
    deepScannedRepositories: number;
    deepScanLimit: number;
    completeRepositoryScans: number;
    deepScanErrors: number;
    accountAttributedRepositories: number;
    accountAttributedCommits: number;
    sampledAccountAttributedCommits: number;
    signedCommitCount: number;
    identityConfirmed: boolean;
    apiCalls: number;
    rateLimitRemaining: number | null;
    analysisSeconds: number;
    linkedinSignals: { provided: boolean };
    publicActivity: {
      available: boolean;
      eventsReviewed: number;
      pushEvents: number;
      pushedCommits: number;
      pullRequestsOpened: number;
      pullRequestsMerged: number;
      externalRepositories: string[];
    };
    projects: {
      name: string;
      url: string;
      description: string;
      language: string | null;
      pushedAt: string | null;
      languages: string[];
      accountAttributedCommits: number;
      sampledAccountAttributedCommits: number;
      commitCountCapped: boolean;
      signedCommits: number;
      accountContributionShare: number;
      totalContributors: number;
      sampleCommitAdditions: number;
      sampleCommitDeletions: number;
      sampleCommitFilesChanged: number;
      firstAccountAttributedCommit: string | null;
      lastAccountAttributedCommit: string | null;
      sampleCommitUrls: string[];
    }[];
  };
};

export type AnalysisResponse = {
  success: boolean;
  error?: string;
  analysis?: CareerAnalysis;
};
