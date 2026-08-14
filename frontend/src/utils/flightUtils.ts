export function calculateFlightDuration(
  departureTime: string,
  arrivalTime: string
): string {
  if (!departureTime || !arrivalTime) return '';

  const [depHours, depMinutes] = departureTime.split(":").map(Number);
  const [arrHours, arrMinutes] = arrivalTime.split(":").map(Number);

  let departure = depHours * 60 + depMinutes;
  let arrival = arrHours * 60 + arrMinutes;

  // Handle overnight flights
  if (arrival < departure) {
    arrival += 24 * 60;
  }

  const duration = arrival - departure;

  const hours = Math.floor(duration / 60);
  const minutes = duration % 60;

  if (minutes === 0) {
    return `${hours}h`;
  }

  return `${hours}h ${minutes}m`;
}
