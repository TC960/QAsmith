import { useState } from "react";
import { Hero } from "@/components/Hero";
import { CrawlingStatus } from "@/components/CrawlingStatus";
import { SiteInfo } from "@/components/SiteInfo";
import { TestCases } from "@/components/TestCases";
import { TestReport } from "@/components/TestReport";
import { WorkflowStepper } from "@/components/WorkflowStepper";

type Step = "input" | "crawling" | "site-info" | "test-cases" | "report";

const Index = () => {
  const [currentStep, setCurrentStep] = useState<Step>("input");
  const [url, setUrl] = useState("");
  const [selectedPages, setSelectedPages] = useState<string[]>([]);

  const handleUrlSubmit = (submittedUrl: string) => {
    setUrl(submittedUrl);
    setCurrentStep("crawling");
    
    // Simulate crawling
    setTimeout(() => {
      setCurrentStep("site-info");
    }, 3000);
  };

  const handlePagesSelected = (pages: string[]) => {
    setSelectedPages(pages);
    setCurrentStep("test-cases");
  };

  const handleTestsGenerated = () => {
    setCurrentStep("report");
  };

  const handleReset = () => {
    setCurrentStep("input");
    setUrl("");
    setSelectedPages([]);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-12 text-center">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent mb-3">
            QASmith
          </h1>
          <p className="text-muted-foreground text-lg">
            AI-Powered Website Testing
          </p>
        </header>

        <WorkflowStepper currentStep={currentStep} />

        <div className="mt-12">
          {currentStep === "input" && (
            <Hero onSubmit={handleUrlSubmit} />
          )}
          
          {currentStep === "crawling" && (
            <CrawlingStatus url={url} />
          )}
          
          {currentStep === "site-info" && (
            <SiteInfo url={url} onNext={handlePagesSelected} />
          )}
          
          {currentStep === "test-cases" && (
            <TestCases 
              selectedPages={selectedPages} 
              onNext={handleTestsGenerated}
            />
          )}
          
          {currentStep === "report" && (
            <TestReport 
              url={url}
              selectedPages={selectedPages}
              onReset={handleReset}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Index;
