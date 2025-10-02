import { Loader2, Globe } from "lucide-react";
import { Card } from "@/components/ui/card";

interface CrawlingStatusProps {
  url: string;
}

export const CrawlingStatus = ({ url }: CrawlingStatusProps) => {
  return (
    <div className="max-w-2xl mx-auto">
      <Card className="p-12 text-center bg-gradient-to-br from-card via-card to-muted/20">
        <div className="flex flex-col items-center gap-6">
          <div className="relative">
            <Globe className="w-16 h-16 text-primary animate-pulse" />
            <Loader2 className="w-8 h-8 text-accent absolute -top-2 -right-2 animate-spin" />
          </div>
          
          <div>
            <h3 className="text-2xl font-bold mb-2">Crawling Website</h3>
            <p className="text-muted-foreground mb-1">Analyzing structure and pages</p>
            <p className="text-sm text-primary font-mono">{url}</p>
          </div>
          
          <div className="w-full max-w-md space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="text-primary font-medium">Discovering pages...</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-primary to-accent animate-pulse w-2/3" />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
