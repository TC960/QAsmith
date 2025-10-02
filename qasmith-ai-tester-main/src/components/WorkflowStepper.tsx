import { Check, Globe, FileSearch, FlaskConical, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

type Step = "input" | "crawling" | "site-info" | "test-cases" | "report";

interface WorkflowStepperProps {
  currentStep: Step;
}

const steps = [
  { id: "input", label: "URL Input", icon: Globe },
  { id: "crawling", label: "Crawling", icon: FileSearch },
  { id: "site-info", label: "Site Analysis", icon: FileText },
  { id: "test-cases", label: "Test Cases", icon: FlaskConical },
  { id: "report", label: "Report", icon: FileText },
];

export const WorkflowStepper = ({ currentStep }: WorkflowStepperProps) => {
  const currentIndex = steps.findIndex(s => s.id === currentStep);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex;
          
          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all",
                    isActive && "border-primary bg-primary text-primary-foreground shadow-glow",
                    isCompleted && "border-accent bg-accent text-accent-foreground",
                    !isActive && !isCompleted && "border-muted bg-background text-muted-foreground"
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-6 h-6" />
                  ) : (
                    <Icon className="w-6 h-6" />
                  )}
                </div>
                <span
                  className={cn(
                    "text-sm mt-2 font-medium transition-colors",
                    isActive && "text-primary",
                    isCompleted && "text-accent",
                    !isActive && !isCompleted && "text-muted-foreground"
                  )}
                >
                  {step.label}
                </span>
              </div>
              
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    "h-0.5 flex-1 mx-2 transition-colors",
                    index < currentIndex ? "bg-accent" : "bg-muted"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
