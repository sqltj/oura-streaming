import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface DataPoint {
  label: string;
  value: number;
}

interface MetricChartProps {
  title: string;
  data: DataPoint[];
  color?: string;
  unit?: string;
}

export function MetricChart({
  title,
  data,
  color = "#6366f1",
  unit = "",
}: MetricChartProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium tracking-wide text-muted-foreground uppercase">
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex h-[200px] items-center justify-center">
          <p className="text-sm text-muted-foreground">No data yet</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-baseline justify-between">
          <CardTitle className="text-sm font-medium tracking-wide text-muted-foreground uppercase">
            {title}
          </CardTitle>
          {data.length > 0 && (
            <span className="font-mono text-2xl font-light tabular-nums">
              {data[data.length - 1].value}
              {unit && (
                <span className="ml-1 text-xs text-muted-foreground">{unit}</span>
              )}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" opacity={0.5} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: "#a3a3a3" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#a3a3a3" }}
              axisLine={false}
              tickLine={false}
              width={35}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fafafa",
                border: "1px solid #e5e5e5",
                borderRadius: "6px",
                fontSize: "12px",
              }}
              formatter={(value: number) => [`${value}${unit}`, title]}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
