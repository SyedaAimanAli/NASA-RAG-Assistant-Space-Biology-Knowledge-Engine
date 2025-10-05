import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";

interface Document {
  id: string;
  title: string;
  score: number;
  snippet?: string;
}

interface DocumentPanelProps {
  documents: Document[];
  isVisible: boolean;
}

export function DocumentPanel({ documents, isVisible }: DocumentPanelProps) {
  if (!isVisible) return null;

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 shrink-0">
        <CardTitle className="flex items-center gap-2 text-lg">
          <FileText className="h-5 w-5" />
          Retrieved Documents
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-3 p-4 pt-0">
            {documents.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No documents retrieved yet
              </p>
            ) : (
              documents.map((doc) => (
                <Card key={doc.id} className="p-3 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-sm leading-tight">{doc.title}</h4>
                    <Badge variant="secondary" className="ml-2 shrink-0">
                      {(doc.score * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  {doc.snippet && (
                    <p className="text-xs text-muted-foreground line-clamp-3">
                      {doc.snippet}
                    </p>
                  )}
                </Card>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}