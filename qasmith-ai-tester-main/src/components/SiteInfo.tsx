import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { FileText, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

interface SiteInfoProps {
  url: string;
  onNext: (selectedPages: string[]) => void;
}

// Mock data
const mockPages = [
  { path: "/", title: "Home", importance: "high" },
  { path: "/about", title: "About Us", importance: "high" },
  { path: "/products", title: "Products", importance: "high" },
  { path: "/products/item-1", title: "Product Item 1", importance: "medium" },
  { path: "/products/item-2", title: "Product Item 2", importance: "medium" },
  { path: "/contact", title: "Contact", importance: "high" },
  { path: "/blog", title: "Blog", importance: "medium" },
  { path: "/blog/post-1", title: "Blog Post 1", importance: "low" },
  { path: "/pricing", title: "Pricing", importance: "high" },
];

const mockStats = {
  totalPages: 9,
  avgLoadTime: "1.2s",
  technologies: ["React", "Tailwind CSS", "Vite"],
};

export const SiteInfo = ({ url, onNext }: SiteInfoProps) => {
  const [selectedPages, setSelectedPages] = useState<string[]>([]);

  const handleToggle = (path: string) => {
    setSelectedPages(prev =>
      prev.includes(path)
        ? prev.filter(p => p !== path)
        : [...prev, path]
    );
  };

  const handleSelectAll = () => {
    if (selectedPages.length === mockPages.length) {
      setSelectedPages([]);
    } else {
      setSelectedPages(mockPages.map(p => p.path));
    }
  };

  const handleNext = () => {
    if (selectedPages.length === 0) {
      toast.error("Please select at least one page to test");
      return;
    }
    onNext(selectedPages);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <Card className="p-8 bg-gradient-to-br from-card to-muted/10">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="text-2xl font-bold mb-2">Site Analysis Complete</h3>
            <p className="text-muted-foreground font-mono text-sm">{url}</p>
          </div>
          <CheckCircle2 className="w-12 h-12 text-accent" />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-background border border-border">
            <div className="text-3xl font-bold text-primary mb-1">{mockStats.totalPages}</div>
            <div className="text-sm text-muted-foreground">Pages Found</div>
          </div>
          <div className="p-4 rounded-lg bg-background border border-border">
            <div className="text-3xl font-bold text-accent mb-1">{mockStats.avgLoadTime}</div>
            <div className="text-sm text-muted-foreground">Avg Load Time</div>
          </div>
          <div className="p-4 rounded-lg bg-background border border-border">
            <div className="text-sm text-muted-foreground mb-2">Technologies</div>
            <div className="flex flex-wrap gap-1">
              {mockStats.technologies.map(tech => (
                <Badge key={tech} variant="secondary" className="text-xs">{tech}</Badge>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <Card className="p-8">
        <div className="flex items-center justify-between mb-6">
          <h4 className="text-xl font-semibold">Select Pages to Test</h4>
          <Button variant="outline" onClick={handleSelectAll}>
            {selectedPages.length === mockPages.length ? "Deselect All" : "Select All"}
          </Button>
        </div>

        <div className="space-y-3 mb-6">
          {mockPages.map((page) => (
            <div
              key={page.path}
              className="flex items-center gap-3 p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
            >
              <Checkbox
                checked={selectedPages.includes(page.path)}
                onCheckedChange={() => handleToggle(page.path)}
              />
              <FileText className="w-5 h-5 text-muted-foreground" />
              <div className="flex-1">
                <div className="font-medium">{page.title}</div>
                <div className="text-sm text-muted-foreground font-mono">{page.path}</div>
              </div>
              <Badge
                variant={
                  page.importance === "high" ? "default" :
                  page.importance === "medium" ? "secondary" : "outline"
                }
              >
                {page.importance}
              </Badge>
            </div>
          ))}
        </div>

        <div className="flex justify-between items-center">
          <p className="text-sm text-muted-foreground">
            {selectedPages.length} page{selectedPages.length !== 1 ? "s" : ""} selected
          </p>
          <Button onClick={handleNext} size="lg">
            Generate Test Cases
          </Button>
        </div>
      </Card>
    </div>
  );
};
