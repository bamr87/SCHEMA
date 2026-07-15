import { formatDate } from "./lib/format-date";
import { Button } from "./components/Button";

export function main(): void {
  console.log(`acme-app started ${formatDate(new Date())}`, Button);
}
