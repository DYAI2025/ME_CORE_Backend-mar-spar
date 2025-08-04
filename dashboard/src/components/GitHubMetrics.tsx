'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchGitHubRepository, fetchGitHubCommits, fetchGitHubWorkflows, fetchGitHubPullRequests, fetchGitHubIssues } from '@/lib/api'
import { 
  StarIcon,
  EyeIcon,
  CodeBracketIcon,
  CodeBracketSquareIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import clsx from 'clsx'
import { formatDistance } from 'date-fns'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

interface GitHubMetricsProps {
  owner?: string
  repo?: string
}

export function GitHubMetrics({ owner = 'DYAI2025', repo = 'ME_CORE_Backend-mar-spar' }: GitHubMetricsProps) {
  const { data: repository } = useQuery({
    queryKey: ['github-repo', owner, repo],
    queryFn: () => fetchGitHubRepository(owner, repo),
    refetchInterval: 300000, // Refresh every 5 minutes
  })

  const { data: commits } = useQuery({
    queryKey: ['github-commits', owner, repo],
    queryFn: () => fetchGitHubCommits(owner, repo, 20),
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: workflows } = useQuery({
    queryKey: ['github-workflows', owner, repo],
    queryFn: () => fetchGitHubWorkflows(owner, repo),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: pullRequests } = useQuery({
    queryKey: ['github-prs', owner, repo],
    queryFn: () => fetchGitHubPullRequests(owner, repo),
    refetchInterval: 120000, // Refresh every 2 minutes
  })

  const { data: issues } = useQuery({
    queryKey: ['github-issues', owner, repo],
    queryFn: () => fetchGitHubIssues(owner, repo),
    refetchInterval: 300000, // Refresh every 5 minutes
  })

  // Prepare commit activity data for chart
  const commitActivityData = commits ? prepareCommitActivityData(commits) : []
  const workflowStatusData = workflows ? prepareWorkflowStatusData(workflows) : []

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">GitHub Repository Metrics</h2>
        {repository && (
          <a
            href={`https://github.com/${owner}/${repo}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <CodeBracketIcon className="h-4 w-4 mr-2" />
            View on GitHub
          </a>
        )}
      </div>

      {/* Repository Stats */}
      {repository && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Repository Overview</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <StarIcon className="h-8 w-8 text-yellow-500" />
              </div>
              <div className="text-2xl font-bold text-gray-900">{repository.stargazers_count}</div>
              <div className="text-sm text-gray-500">Stars</div>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <CodeBracketSquareIcon className="h-8 w-8 text-blue-500" />
              </div>
              <div className="text-2xl font-bold text-gray-900">{repository.forks_count}</div>
              <div className="text-sm text-gray-500">Forks</div>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
              </div>
              <div className="text-2xl font-bold text-gray-900">{repository.open_issues_count}</div>
              <div className="text-sm text-gray-500">Open Issues</div>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <ClockIcon className="h-8 w-8 text-green-500" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {formatDistance(new Date(repository.updated_at), new Date(), { addSuffix: true })}
              </div>
              <div className="text-sm text-gray-500">Last Updated</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Commit Activity Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Commit Activity (Last 20 commits)</h3>
          {commitActivityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={commitActivityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="commits" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-500">
              Loading commit data...
            </div>
          )}
        </div>

        {/* Workflow Status Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Status Distribution</h3>
          {workflowStatusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={workflowStatusData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#10B981" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-500">
              Loading workflow data...
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Pull Requests */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Pull Requests</h3>
          <div className="space-y-3">
            {pullRequests ? pullRequests.slice(0, 5).map((pr: any) => (
              <div key={pr.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className={clsx(
                  'flex-shrink-0 h-2 w-2 rounded-full mt-2',
                  pr.state === 'open' ? 'bg-green-500' : 
                  pr.merged_at ? 'bg-purple-500' : 'bg-red-500'
                )} />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 truncate">{pr.title}</div>
                  <div className="text-xs text-gray-500">
                    #{pr.number} by {pr.user.login} • {formatDistance(new Date(pr.created_at), new Date(), { addSuffix: true })}
                  </div>
                </div>
                <div className={clsx(
                  'px-2 py-1 rounded text-xs font-medium',
                  pr.state === 'open' ? 'bg-green-100 text-green-800' :
                  pr.merged_at ? 'bg-purple-100 text-purple-800' :
                  'bg-red-100 text-red-800'
                )}>
                  {pr.merged_at ? 'merged' : pr.state}
                </div>
              </div>
            )) : (
              <div className="text-gray-500 text-center py-4">Loading pull requests...</div>
            )}
          </div>
        </div>

        {/* Recent Issues */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Open Issues</h3>
          <div className="space-y-3">
            {issues ? issues.slice(0, 5).map((issue: any) => (
              <div key={issue.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 truncate">{issue.title}</div>
                  <div className="text-xs text-gray-500">
                    #{issue.number} opened {formatDistance(new Date(issue.created_at), new Date(), { addSuffix: true })}
                  </div>
                  {issue.labels && issue.labels.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {issue.labels.slice(0, 3).map((label: any) => (
                        <span
                          key={label.id}
                          className="px-2 py-1 rounded text-xs"
                          style={{
                            backgroundColor: `#${label.color}20`,
                            color: `#${label.color}`
                          }}
                        >
                          {label.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )) : (
              <div className="text-gray-500 text-center py-4">Loading issues...</div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Workflows */}
      {workflows && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Workflow Runs</h3>
          <div className="space-y-3">
            {workflows.slice(0, 8).map((workflow: any) => (
              <div key={workflow.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  {workflow.conclusion === 'success' ? (
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  ) : workflow.conclusion === 'failure' ? (
                    <XCircleIcon className="h-5 w-5 text-red-500" />
                  ) : workflow.status === 'in_progress' ? (
                    <ClockIcon className="h-5 w-5 text-blue-500" />
                  ) : (
                    <ClockIcon className="h-5 w-5 text-gray-400" />
                  )}
                  <div>
                    <div className="text-sm font-medium text-gray-900">{workflow.name}</div>
                    <div className="text-xs text-gray-500">
                      {workflow.head_branch} • {formatDistance(new Date(workflow.created_at), new Date(), { addSuffix: true })}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={clsx(
                    'px-2 py-1 rounded text-xs font-medium',
                    workflow.conclusion === 'success' ? 'bg-green-100 text-green-800' :
                    workflow.conclusion === 'failure' ? 'bg-red-100 text-red-800' :
                    workflow.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  )}>
                    {workflow.conclusion || workflow.status}
                  </div>
                  <a
                    href={workflow.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-xs"
                  >
                    View
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Helper functions for data preparation
function prepareCommitActivityData(commits: any[]) {
  const commitsByDate = commits.reduce((acc, commit) => {
    const date = new Date(commit.commit.author.date).toISOString().split('T')[0]
    acc[date] = (acc[date] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return Object.entries(commitsByDate)
    .map(([date, count]) => ({ date, commits: count }))
    .sort((a, b) => a.date.localeCompare(b.date))
}

function prepareWorkflowStatusData(workflows: any[]) {
  const statusCount = workflows.reduce((acc, workflow) => {
    const status = workflow.conclusion || workflow.status
    acc[status] = (acc[status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return Object.entries(statusCount).map(([status, count]) => ({ status, count }))
}