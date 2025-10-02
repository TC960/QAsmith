import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";

interface HeroProps {
  onSubmit: (url: string) => void;
}

export const Hero = ({ onSubmit }: HeroProps) => {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      toast.error("Please enter a URL");
      return;
    }

    // Basic URL validation
    try {
      new URL(url);
      onSubmit(url);
    } catch {
      toast.error("Please enter a valid URL");
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-primary/5 via-background to-accent/5 p-12 shadow-lg">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
        
        <div className="relative z-10">
          <div className="flex items-center justify-center mb-6">
            <Sparkles className="w-12 h-12 text-primary" />
          </div>
          
          <h2 className="text-3xl font-bold text-center mb-4">
            Test Any Website with AI
          </h2>
          
          <p className="text-center text-muted-foreground mb-8 max-w-2xl mx-auto">
            Enter your website URL and let our AI crawl, analyze, and create comprehensive test cases automatically.
          </p>
          
          <form onSubmit={handleSubmit} className="flex gap-3">
            <Input
              type="url"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1 h-14 text-lg"
            />
            <Button type="submit" size="lg" className="h-14 px-8">
              Start Testing
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};
