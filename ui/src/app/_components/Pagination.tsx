import Link from "next/link";
import styles from "./appShell.module.css";

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function withParams(basePath: string, params: Record<string, string>) {
  const sp = new URLSearchParams(params);
  const qs = sp.toString();
  return qs ? `${basePath}?${qs}` : basePath;
}

export default function Pagination({
  basePath,
  page,
  pageSize,
  total,
  params,
}: {
  basePath: string;
  page: number;
  pageSize: number;
  total: number;
  params: Record<string, string>;
}) {
  const totalPages = Math.max(1, Math.ceil(total / Math.max(1, pageSize)));
  const p = clamp(page, 1, totalPages);

  const prev = p > 1 ? p - 1 : null;
  const next = p < totalPages ? p + 1 : null;

  const from = total ? (p - 1) * pageSize + 1 : 0;
  const to = Math.min(total, p * pageSize);

  return (
    <div className={styles.actions} style={{ justifyContent: "space-between", width: "100%" }}>
      <div className={styles.meta}>
        {total ? (
          <>
            Showing <strong>{from}</strong>–<strong>{to}</strong> of <strong>{total}</strong>
          </>
        ) : (
          <>No results</>
        )}
      </div>

      <div className={styles.actions}>
        {prev ? (
          <Link className={styles.actionLink} href={withParams(basePath, { ...params, page: String(prev) })}>
            Prev
          </Link>
        ) : (
          <span className={styles.meta}>Prev</span>
        )}
        <span className={styles.meta}>
          Page {p} / {totalPages}
        </span>
        {next ? (
          <Link className={styles.actionLink} href={withParams(basePath, { ...params, page: String(next) })}>
            Next
          </Link>
        ) : (
          <span className={styles.meta}>Next</span>
        )}
      </div>
    </div>
  );
}
