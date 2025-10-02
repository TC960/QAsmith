import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, Play } from "lucide-react";
import { toast } from "sonner";

interface TestCasesProps {
  selectedPages: string[];
  onNext: () => void;
}

type TestStatus = "pending" | "passed" | "failed";
type TestPriority = "high" | "medium";

interface TestCase {
  id: string;
  page: string;
  title: string;
  description: string;
  priority: TestPriority;
  status: TestStatus;
}

// Mock test cases
const generateMockTestCases = (pages: string[]): TestCase[] => {
  return pages.flatMap(page => [
    {
      id: `${page}-1`,
      page,
      title: "Page Load Performance",
      description: "Verify page loads within 3 seconds",
      priority: "high" as TestPriority,
      status: "pending" as TestStatus,
    },
    {
      id: `${page}-2`,
      page,
      title: "Responsive Design Check",
      description: "Test layout on mobile, tablet, and desktop viewports",
      priority: "high" as TestPriority,
      status: "pending" as TestStatus,
    },
    {
      id: `${page}-3`,
      page,
      title: "Link Validation",
      description: "Ensure all links are functional and lead to valid destinations",
      priority: "medium" as TestPriority,
      status: "pending" as TestStatus,
    },
    {
      id: `${page}-4`,
      page,
      title: "Form Input Validation",
      description: "Test form fields with valid and invalid data",
      priority: "medium" as TestPriority,
      status: "pending" as TestStatus,
    },
    {
      id: `${page}-5`,
      page,
      title: "Accessibility Compliance",
      description: "Check WCAG 2.1 AA compliance for screen readers and keyboard navigation",
      priority: "high" as TestPriority,
      status: "pending" as TestStatus,
    },
  ]);
};

export const TestCases = ({ selectedPages, onNext }: TestCasesProps) => {
  const [isGenerating, setIsGenerating] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [runningTests, setRunningTests] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Simulate AI generation
    const timer = setTimeout(() => {
      setTestCases(generateMockTestCases(selectedPages));
      setIsGenerating(false);
      toast.success(`Generated ${selectedPages.length * 5} test cases`);
    }, 2000);

    return () => clearTimeout(timer);
  }, [selectedPages]);

  const handleRunTests = () => {
    setIsRunning(true);
    const tests = testCases.map(tc => tc.id);
    
    // Simulate running tests one by one
    tests.forEach((testId, index) => {
      setTimeout(() => {
        setRunningTests(prev => new Set([...prev, testId]));
        
          setTimeout(() => {
          setTestCases(prev =>
            prev.map(tc =>
              tc.id === testId
                ? { ...tc, status: (Math.random() > 0.1 ? "passed" : "failed") as TestStatus }
                : tc
            )
          );
          setRunningTests(prev => {
            const next = new Set(prev);
            next.delete(testId);
            return next;
          });

          // All done
          if (index === tests.length - 1) {
            setIsRunning(false);
            setTimeout(() => {
              onNext();
            }, 500);
          }
        }, 300);
      }, index * 350);
    });
  };

  if (isGenerating) {
    return (
      <div className="max-w-3xl mx-auto">
        <Card className="p-12 text-center bg-gradient-to-br from-card to-muted/10">
          <div className="flex flex-col items-center gap-6">
            <Sparkles className="w-16 h-16 text-primary animate-pulse" />
            <div>
              <h3 className="text-2xl font-bold mb-2">Generating Test Cases</h3>
              <p className="text-muted-foreground">AI is creating comprehensive tests for your pages...</p>
            </div>
            <Loader2 className="w-8 h-8 text-accent animate-spin" />
          </div>
        </Card>
      </div>
    );
  }

  const passedCount = testCases.filter(tc => tc.status === "passed").length;
  const failedCount = testCases.filter(tc => tc.status === "failed").length;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <Card className="p-8 bg-gradient-to-br from-card to-muted/10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold mb-2">AI-Generated Test Cases</h3>
            <p className="text-muted-foreground">
              {testCases.length} tests across {selectedPages.length} pages
            </p>
          </div>
          <Button
            onClick={handleRunTests}
            disabled={isRunning}
            size="lg"
            className="gap-2"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Running Tests...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run All Tests
              </>
            )}
          </Button>
        </div>

        {(passedCount > 0 || failedCount > 0) && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="p-4 rounded-lg bg-background border border-border">
              <div className="text-2xl font-bold text-foreground mb-1">{testCases.length}</div>
              <div className="text-sm text-muted-foreground">Total Tests</div>
            </div>
            <div className="p-4 rounded-lg bg-background border border-accent/50">
              <div className="text-2xl font-bold text-accent mb-1">{passedCount}</div>
              <div className="text-sm text-muted-foreground">Passed</div>
            </div>
            <div className="p-4 rounded-lg bg-background border border-destructive/50">
              <div className="text-2xl font-bold text-destructive mb-1">{failedCount}</div>
              <div className="text-sm text-muted-foreground">Failed</div>
            </div>
          </div>
        )}
      </Card>

      <div className="space-y-4">
        {selectedPages.map(page => {
          const pageTests = testCases.filter(tc => tc.page === page);
          
          return (
            <Card key={page} className="p-6">
              <h4 className="font-semibold mb-4 flex items-center gap-2">
                <span className="text-primary font-mono">{page}</span>
                <Badge variant="outline">{pageTests.length} tests</Badge>
              </h4>
              
              <div className="space-y-3">
                {pageTests.map(test => (
                  <div
                    key={test.id}
                    className="flex items-start gap-3 p-4 rounded-lg border border-border"
                  >
                    <div className="flex-1">
                      <div className="font-medium mb-1">{test.title}</div>
                      <div className="text-sm text-muted-foreground">{test.description}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={test.priority === "high" ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {test.priority}
                      </Badge>
                      {runningTests.has(test.id) && (
                        <Loader2 className="w-4 h-4 animate-spin text-primary" />
                      )}
                      {test.status === "passed" && (
                        <Badge className="bg-accent text-accent-foreground">Passed</Badge>
                      )}
                      {test.status === "failed" && (
                        <Badge variant="destructive">Failed</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
