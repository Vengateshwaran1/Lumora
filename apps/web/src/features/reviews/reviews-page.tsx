import { useQuery } from "@tanstack/react-query";
import { MessageCircle } from "lucide-react";
import { Link } from "react-router-dom";

import { PreviewBadge } from "@/shared/components/preview-badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { listMockReviews } from "@/shared/mocks/api";
import { ReviewStatusBadge } from "@/shared/mocks/badges";

export function ReviewsPage() {
  const reviewsQuery = useQuery({ queryKey: ["mock", "reviews"], queryFn: listMockReviews });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Reviews</h1>
          <p className="text-muted-foreground text-sm">AI proposes → human reviews → approves.</p>
        </div>
        <PreviewBadge />
      </div>

      <div className="flex flex-col gap-2">
        {reviewsQuery.isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-16 rounded-lg" />
            ))
          : reviewsQuery.data?.map((review) => (
              <Link
                key={review.id}
                to={`/app/pull-requests/${review.prId}`}
                className="surface-card-interactive flex items-center justify-between gap-3 p-4"
              >
                <div>
                  <p className="text-sm font-medium">{review.prTitle}</p>
                  <div className="text-muted-foreground mt-0.5 flex items-center gap-3 text-xs">
                    <span>{review.repository}</span>
                    <span>·</span>
                    <span>{review.reviewer === "agent" ? "Reviewer Agent" : "human reviewer"}</span>
                    {review.comments > 0 ? (
                      <span className="flex items-center gap-1">
                        <MessageCircle className="size-3" />
                        {review.comments}
                      </span>
                    ) : null}
                  </div>
                </div>
                <ReviewStatusBadge status={review.status} />
              </Link>
            ))}
      </div>
    </div>
  );
}
