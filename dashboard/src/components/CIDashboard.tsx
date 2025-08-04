'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchCIMetrics, CIMetrics, calculateRepositoryHealth } from '@/lib/api'
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon,
  ArrowPathIcon,
  ChartBarIcon,
  CodeBracketIcon,
  UsersIcon
} from '@heroicons/react/24/outline'
import clsx from 'clsx'
import { formatDistance } from 'date-fns'

interface CIDashboardProps {
  owner?: string
  repo?: string
}

export function CIDashboard({ owner = 'DYAI2025', repo = 'ME_CORE_Backend-mar-spar' }: CIDashboardProps) {
  const { data: ciMetrics, isLoading, error } = useQuery({
    queryKey: ['ci-metrics', owner, repo],
    queryFn: () => fetchCIMetrics(owner, repo),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6">
                <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error || !ciMetrics) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Failed to load CI/CD metrics</p>
      </div>
    )
  }

  const repositoryHealth = calculateRepositoryHealth(ciMetrics)

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">CI/CD Dashboard</h1>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Repository Health:</span>
          <div className={clsx(
            'px-3 py-1 rounded-full text-sm font-medium',
            repositoryHealth.score >= 80 ? 'bg-green-100 text-green-800' :
            repositoryHealth.score >= 60 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          )}>
            {repositoryHealth.score}%
          </div>
        </div>
      </div>

      {/* Repository Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Repository Overview</h2>
          <CodeBracketIcon className="h-6 w-6 text-gray-400" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{ciMetrics.github.repository.stargazers_count}</div>
            <div className="text-sm text-gray-500">Stars</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{ciMetrics.github.repository.forks_count}</div>
            <div className="text-sm text-gray-500">Forks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{ciMetrics.github.repository.open_issues_count}</div>
            <div className="text-sm text-gray-500">Open Issues</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{ciMetrics.github.recent_commits.length}</div>
            <div className="text-sm text-gray-500">Recent Commits</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GitHub Actions */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">GitHub Actions</h2>
            <ChartBarIcon className="h-6 w-6 text-gray-400" />
          </div>
          <div className="space-y-3">
            {ciMetrics.github.workflows.slice(0, 5).map((workflow) => (
              <div key={workflow.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  {getWorkflowStatusIcon(workflow.conclusion, workflow.status)}
                  <div>
                    <div className="font-medium text-gray-900">{workflow.name}</div>
                    <div className="text-sm text-gray-500">
                      {formatDistance(new Date(workflow.updated_at), new Date(), { addSuffix: true })}
                    </div>
                  </div>
                </div>
                <div className={clsx(
                  'px-2 py-1 rounded text-xs font-medium',
                  getWorkflowStatusColor(workflow.conclusion, workflow.status)
                )}>
                  {workflow.conclusion || workflow.status}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Jenkins Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Jenkins CI/CD</h2>
            <div className={clsx(
              'px-2 py-1 rounded text-xs font-medium',
              ciMetrics.jenkins?.healthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            )}>
              {ciMetrics.jenkins?.healthy ? 'Healthy' : 'Unhealthy'}
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">Queue Size</div>
                <div className="text-xl font-bold text-gray-900">{ciMetrics.jenkins?.queueSize || 0}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Executors</div>
                <div className="text-xl font-bold text-gray-900">
                  {ciMetrics.jenkins?.busyExecutors || 0} / {ciMetrics.jenkins?.totalExecutors || 0}
                </div>
              </div>
            </div>

            {ciMetrics.jenkins?.recentBuilds && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-900">Recent Builds</div>
                {ciMetrics.jenkins.recentBuilds.slice(0, 3).map((build, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center space-x-2">
                      {getJenkinsStatusIcon(build.result)}
                      <span className="text-sm text-gray-700 truncate">{build.displayName}</span>
                    </div>
                    <span className={clsx('text-xs', getJenkinsStatusColor(build.result))}>
                      {build.result}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Results */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h2>
          <div className="space-y-3">
            {ciMetrics.test_results.slice(0, 5).map((test) => (
              <div key={test.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium text-gray-900 capitalize">{test.type} Tests</div>
                  <div className="text-sm text-gray-500">
                    {test.passed} passed, {test.failed} failed
                    {test.coverage && ` • ${test.coverage}% coverage`}
                  </div>
                </div>
                <div className={clsx(
                  'px-2 py-1 rounded text-xs font-medium',
                  test.status === 'passed' ? 'bg-green-100 text-green-800' :
                  test.status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                )}>
                  {test.status}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Commits */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Commits</h2>
            <UsersIcon className="h-6 w-6 text-gray-400" />
          </div>
          <div className="space-y-3">
            {ciMetrics.github.recent_commits.slice(0, 5).map((commit) => (
              <div key={commit.sha} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <img
                  src={commit.author?.avatar_url}
                  alt={commit.author?.login}
                  className="h-8 w-8 rounded-full"
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{commit.commit.message}</div>
                  <div className="text-xs text-gray-500">
                    by {commit.commit.author.name} • {formatDistance(new Date(commit.commit.author.date), new Date(), { addSuffix: true })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Repository Health Breakdown */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Repository Health Breakdown</h2>
        <div className="space-y-4">
          {Object.entries(repositoryHealth.factors).map(([key, factor]) => (
            <div key={key}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-900 capitalize">
                  {factor.description}
                </span>
                <span className="text-sm text-gray-500">{Math.round(factor.score)}%</span>
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div
                  className={clsx(
                    'h-2 rounded-full transition-all duration-300',
                    factor.score >= 80 ? 'bg-green-500' :
                    factor.score >= 60 ? 'bg-yellow-500' :
                    'bg-red-500'
                  )}
                  style={{ width: `${factor.score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function getWorkflowStatusIcon(conclusion: string | null, status: string) {
  if (status === 'in_progress') {
    return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />
  }
  
  switch (conclusion) {
    case 'success':
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />
    case 'failure':
      return <XCircleIcon className="h-5 w-5 text-red-500" />
    case 'cancelled':
      return <XCircleIcon className="h-5 w-5 text-gray-500" />
    default:
      return <ClockIcon className="h-5 w-5 text-gray-400" />
  }
}

function getWorkflowStatusColor(conclusion: string | null, status: string) {
  if (status === 'in_progress') {
    return 'bg-blue-100 text-blue-800'
  }
  
  switch (conclusion) {
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'failure':
      return 'bg-red-100 text-red-800'
    case 'cancelled':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function getJenkinsStatusIcon(result: string) {
  switch (result) {
    case 'SUCCESS':
      return <CheckCircleIcon className="h-4 w-4 text-green-500" />
    case 'FAILURE':
      return <XCircleIcon className="h-4 w-4 text-red-500" />
    case 'IN_PROGRESS':
      return <ArrowPathIcon className="h-4 w-4 text-blue-500 animate-spin" />
    default:
      return <ClockIcon className="h-4 w-4 text-gray-400" />
  }
}

function getJenkinsStatusColor(result: string) {
  switch (result) {
    case 'SUCCESS':
      return 'text-green-600'
    case 'FAILURE':
      return 'text-red-600'
    case 'IN_PROGRESS':
      return 'text-blue-600'
    default:
      return 'text-gray-600'
  }
}