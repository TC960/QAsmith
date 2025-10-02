import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, AlertCircle, TrendingUp, Download, RotateCcw } from "lucide-react";
import { toast } from "sonner";

interface TestReportProps {
  url: string;
  selectedPages: string[];
  onReset: () => void;
}

// Mock report data
const mockReportData = {
  overallScore: 87,
  totalTests: 45,
  passed: 39,
  failed: 4,
  warnings: 2,
  executionTime: "2m 34s",
  insights: [
    {
      type: "success" as const,
      title: "Excellent Performance",
      description: "All pages load within acceptable time limits. Average load time: 1.2s",
    },
    {
      type: "warning" as const,
      title: "Mobile Responsiveness",
      description: "Some elements on /products page may overflow on smaller screens",
    },
    {
      type: "error" as const,
      title: "Accessibility Issues",
      description: "4 pages missing proper ARIA labels for interactive elements",
    },
    {
      type: "success" as const,
      title: "Security Headers",
      description: "All recommended security headers are properly configured",
    },
  ],
  pageScores: [
    { page: "/", score: 95 },
    { page: "/about", score: 90 },
    { page: "/products", score: 78 },
    { page: "/contact", score: 92 },
    { page: "/pricing", score: 88 },
  ],
  recommendations: [
    "Add aria-label attributes to icon buttons on product pages",
    "Optimize image sizes on the products listing page",
    "Implement lazy loading for below-the-fold content",
    "Add error state handling for form submissions",
  ],
};

export const TestReport = ({ url, selectedPages, onReset }: TestReportProps) => {
  const handleDownload = () => {
    toast.success("Report downloaded successfully");
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-accent";
    if (score >= 70) return "text-primary";
    return "text-destructive";
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card className="p-8 bg-gradient-to-br from-primary/10 via-card to-accent/10">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="text-3xl font-bold mb-2">Test Report</h3>
            <p className="text-muted-foreground font-mono text-sm">{url}</p>
            <p className="text-sm text-muted-foreground mt-1">
              Tested {selectedPages.length} pages • Completed in {mockReportData.executionTime}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleDownload} className="gap-2">
              <Download className="w-4 h-4" />
              Export
            </Button>
            <Button onClick={onReset} className="gap-2">
              <RotateCcw className="w-4 h-4" />
              New Test
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex-1 text-center p-6 rounded-lg bg-background border-2 border-primary">
            <div className={`text-5xl font-bold ${getScoreColor(mockReportData.overallScore)} mb-2`}>
              {mockReportData.overallScore}
            </div>
            <div className="text-sm text-muted-foreground">Overall Score</div>
          </div>
          
          <div className="flex-1 grid grid-cols-3 gap-4">
            <div className="text-center p-4 rounded-lg bg-background border border-border">
              <div className="flex items-center justify-center gap-1 mb-1">
                <CheckCircle2 className="w-5 h-5 text-accent" />
                <div className="text-2xl font-bold">{mockReportData.passed}</div>
              </div>
              <div className="text-xs text-muted-foreground">Passed</div>
            </div>
            <div className="text-center p-4 rounded-lg bg-background border border-border">
              <div className="flex items-center justify-center gap-1 mb-1">
                <XCircle className="w-5 h-5 text-destructive" />
                <div className="text-2xl font-bold">{mockReportData.failed}</div>
              </div>
              <div className="text-xs text-muted-foreground">Failed</div>
            </div>
            <div className="text-center p-4 rounded-lg bg-background border border-border">
              <div className="flex items-center justify-center gap-1 mb-1">
                <AlertCircle className="w-5 h-5 text-primary" />
                <div className="text-2xl font-bold">{mockReportData.warnings}</div>
              </div>
              <div className="text-xs text-muted-foreground">Warnings</div>
            </div>
          </div>
        </div>
      </Card>

      {/* AI Insights */}
      <Card className="p-8">
        <h4 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary" />
          AI Insights
        </h4>
        <div className="space-y-3">
          {mockReportData.insights.map((insight, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-4 rounded-lg border border-border"
            >
              {insight.type === "success" && (
                <CheckCircle2 className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" />
              )}
              {insight.type === "warning" && (
                <AlertCircle className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
              )}
              {insight.type === "error" && (
                <XCircle className="w-5 h-5 text-destructive mt-0.5 flex-shrink-0" />
              )}
              <div className="flex-1">
                <div className="font-medium mb-1">{insight.title}</div>
                <div className="text-sm text-muted-foreground">{insight.description}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Page Scores */}
      <Card className="p-8">
        <h4 className="text-xl font-semibold mb-4">Page Scores</h4>
        <div className="space-y-3">
          {mockReportData.pageScores.map((page) => (
            <div key={page.page} className="flex items-center gap-4">
              <div className="flex-1">
                <div className="font-mono text-sm mb-1">{page.page}</div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-accent transition-all"
                    style={{ width: `${page.score}%` }}
                  />
                </div>
              </div>
              <div className={`text-2xl font-bold ${getScoreColor(page.score)} w-16 text-right`}>
                {page.score}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Recommendations */}
      <Card className="p-8">
        <h4 className="text-xl font-semibold mb-4">Recommendations</h4>
        <div className="space-y-2">
          {mockReportData.recommendations.map((rec, index) => (
            <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
              <Badge variant="outline" className="mt-0.5">{index + 1}</Badge>
              <div className="text-sm flex-1">{rec}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
