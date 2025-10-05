import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { BarChart3 } from "lucide-react";

interface Study {
  title: string;
  score: number;
}

interface StudiesChartProps {
  studies: Study[];
  isVisible: boolean;
}

export function StudiesChart({ studies, isVisible }: StudiesChartProps) {
  if (!isVisible) return null;

  // Transform data for recharts
  const chartData = studies.map(study => ({
    title: study.title.length > 20 ? study.title.substring(0, 20) + "..." : study.title,
    fullTitle: study.title,
    score: Math.round(study.score * 100)
  }));

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 shrink-0">
        <CardTitle className="flex items-center gap-2 text-lg">
          <BarChart3 className="h-5 w-5" />
          Top Related Studies
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden">
        {studies.length === 0 ? (
          <div className="text-muted-foreground text-center py-8">
            No studies data available
          </div>
        ) : (
          <div className="h-full w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="horizontal"
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  type="number" 
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                />
                <YAxis 
                  type="category" 
                  dataKey="title" 
                  width={120}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip 
                  formatter={(value, name, props) => [`${value}%`, "Relevance Score"]}
                  labelFormatter={(label, payload) => payload?.[0]?.payload?.fullTitle || label}
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px'
                  }}
                />
                <Bar 
                  dataKey="score" 
                  fill="hsl(var(--primary))"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}