import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
} from 'react';

import { Flag } from 'lucide-react';

import {
  DjangoApi,
  subscribeToSessionInvalidation,
} from '../api/django.service';

import type {
  DSubscriptionReport,
  DSubscriptionReportInput,
  DSubscriptionReportReason,
} from '../api/types';


const REASONS: ReadonlyArray<{
  value: DSubscriptionReportReason;
  label: string;
}> = [
  {
    value: 'MISSING_BENEFITS',
    label: 'Beneficios no entregados',
  },
  {
    value: 'NO_RESPONSE',
    label: 'Falta de comunicación',
  },
  {
    value: 'TERMS_NOT_MET',
    label: 'Incumplimiento de condiciones',
  },
  {
    value: 'OTHER',
    label: 'Otro motivo',
  },
];


const isOpenReport = (
  report: DSubscriptionReport,
): boolean => (
  report.status === 'OPEN' ||
  report.status === 'IN_REVIEW'
);


function errorMessage(error: unknown): string {

  return error instanceof Error
    ? error.message
    : 'No fue posible completar la solicitud.';
}


type RequestScope = {
  controller: AbortController;
  busy: boolean;
};


interface ReportContextValue {

  reports: DSubscriptionReport[] | null;

  busy: boolean;

  create: (
    data: DSubscriptionReportInput,
  ) => Promise<boolean>;

  refresh: () => Promise<void>;
}


const ReportContext = createContext<
  ReportContextValue | null
>(null);


export function useSubscriptionReports() {
  return useContext(ReportContext);
}


function PrivateReportScope({
  ownerId,
  children,
}: {
  ownerId: string;
  children: React.ReactNode;
}) {

  const scopeRef = useRef<RequestScope | null>(null);

  const [reports, setReports] = useState<
    DSubscriptionReport[] | null
  >(null);

  const [busy, setBusy] = useState(false);

  const [error, setError] = useState('');

  const [notice, setNotice] = useState('');

  const [invalidated, setInvalidated] = useState(false);


  const refresh = useCallback(async () => {

    const scope = scopeRef.current;

    if (
      !scope ||
      scope.busy ||
      scope.controller.signal.aborted
    ) {
      return;
    }

    scope.busy = true;

    setBusy(true);
    setError('');
    setNotice('');
    setReports(null);

    try {

      const response = await DjangoApi.subscriptionReports(
        ownerId,
        scope.controller.signal,
      );

      if (
        scopeRef.current !== scope ||
        scope.controller.signal.aborted
      ) {
        return;
      }

      setReports(response.reports);

    } catch (cause) {

      if (
        scopeRef.current === scope &&
        !scope.controller.signal.aborted
      ) {
        setReports(null);
        setError(errorMessage(cause));
      }

    } finally {

      if (scopeRef.current === scope) {
        scope.busy = false;
        setBusy(false);
      }
    }

  }, [ownerId]);


  useEffect(() => {

    const scope: RequestScope = {
      controller: new AbortController(),
      busy: false,
    };

    scopeRef.current = scope;

    setInvalidated(false);
    setReports(null);
    setError('');
    setNotice('');

    const unsubscribe = subscribeToSessionInvalidation(
      () => {

        scope.controller.abort();

        if (scopeRef.current === scope) {

          scopeRef.current = null;

          setReports(null);
          setBusy(false);
          setNotice('');
          setInvalidated(true);

          setError(
            'Tu sesión ya no está disponible. ' +
            'Vuelve a iniciar sesión.',
          );
        }
      },
    );

    void refresh();

    return () => {

      unsubscribe();

      scope.controller.abort();

      if (scopeRef.current === scope) {
        scopeRef.current = null;
      }
    };

  }, [refresh]);


  const create = async (
    data: DSubscriptionReportInput,
  ): Promise<boolean> => {

    const scope = scopeRef.current;

    if (
      !scope ||
      scope.busy ||
      reports === null ||
      scope.controller.signal.aborted
    ) {
      return false;
    }

    if (reports.some(
      (report) =>
        report.subscription_id === data.subscription_id &&
        isOpenReport(report),
    )) {
      return false;
    }

    scope.busy = true;

    setBusy(true);
    setError('');
    setNotice('');

    try {

      const response =
        await DjangoApi.createSubscriptionReport(
          ownerId,
          data,
          scope.controller.signal,
        );

      if (
        scopeRef.current !== scope ||
        scope.controller.signal.aborted
      ) {
        return false;
      }

      setReports((previous) => [
        response.report,
        ...(previous ?? []).filter(
          (item) => item.id !== response.report.id,
        ),
      ]);

      setNotice(
        `Reporte #${response.report.id} enviado correctamente. ` +
        'La administración revisará tu caso.',
      );

      return true;

    } catch (cause) {

      if (
        scopeRef.current === scope &&
        !scope.controller.signal.aborted
      ) {

        // Un error de red no demuestra que el POST haya fallado.
        // Exigir una nueva consulta antes de permitir otro envio.
        setReports(null);

        setError(
          errorMessage(cause) +
          ' Actualiza tus reportes antes de volver a enviar.',
        );
      }

      return false;

    } finally {

      if (scopeRef.current === scope) {

        scope.busy = false;

        setBusy(false);
      }
    }
  };


  return (
    <ReportContext.Provider
      value={{
        reports,
        busy,
        create,
        refresh,
      }}
    >

      <section
        aria-label="Estado de los reportes"
        className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 space-y-3"
      >

        <div className="flex flex-wrap items-center justify-between gap-3">

          <h4 className="text-sm font-bold text-white">
            Reportes de incumplimiento
          </h4>

          <button
            type="button"
            disabled={busy || invalidated}
            onClick={() => void refresh()}
            className="text-xs font-semibold text-amber-400 hover:text-amber-300 disabled:opacity-40"
          >
            Actualizar reportes
          </button>

        </div>

        <p className="text-xs text-zinc-400">
          Informa problemas con los servicios contratados.
          Tus reportes son privados.
        </p>

        {busy && (
          <p
            role="status"
            className="text-xs text-zinc-400"
          >
            Procesando solicitud...
          </p>
        )}

        {error && (
          <p
            role="alert"
            className="text-sm text-red-400 break-words"
          >
            {error}
          </p>
        )}

        {notice && (
          <p
            role="status"
            className="text-sm text-emerald-400 break-words"
          >
            {notice}
          </p>
        )}

      </section>

      {children}

      <SubscriptionReportHistory />

    </ReportContext.Provider>
  );
}


export function SubscriptionReportScope({
  ownerId,
  children,
}: {
  ownerId: string | null;
  children: React.ReactNode;
}) {

  if (!ownerId) {
    return <>{children}</>;
  }

  return (
    <PrivateReportScope
      key={ownerId}
      ownerId={ownerId}
    >
      {children}
    </PrivateReportScope>
  );
}


export function SubscriptionReportForm({
  membershipId,
  subscriptionTitle,
}: {
  membershipId: string;
  subscriptionTitle: string;
}) {

  const context = useSubscriptionReports();

  const formId = useId();

  const [expanded, setExpanded] = useState(false);

  const [reason, setReason] = useState<
    DSubscriptionReportReason | ''
  >('');

  const [description, setDescription] = useState('');

  const match = /^sus-([1-9][0-9]*)$/.exec(
    membershipId,
  );

  const subscriptionId = match
    ? Number(match[1])
    : 0;

  if (
    !context ||
    !Number.isSafeInteger(subscriptionId) ||
    subscriptionId < 1 ||
    subscriptionId > 2147483647
  ) {
    return null;
  }

  if (context.reports === null) {
    return null;
  }

  const existing = context.reports.find(
    (report) =>
      report.subscription_id === subscriptionId &&
      isOpenReport(report),
  );

  if (existing) {

    return (
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3 space-y-1">

        <p className="text-sm font-semibold text-amber-400">
          Reporte #{existing.id} —
          {' '}
          {existing.status === 'OPEN'
            ? 'Pendiente'
            : 'En revisión'}
        </p>

        <p className="text-xs text-zinc-400">
          Ya existe un reporte abierto para esta membresía.
        </p>

      </div>
    );
  }

  const valid =
    reason !== '' &&
    description.trim().length >= 20 &&
    description.trim().length <= 2000;


  const reset = () => {
    setExpanded(false);
    setReason('');
    setDescription('');
  };


  const submit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {

    event.preventDefault();

    if (
      context.busy ||
      !valid
    ) {
      return;
    }

    const created = await context.create({
      subscription_id: subscriptionId,
      reason,
      description: description.trim(),
    });

    if (created) {
      reset();
    }
  };


  if (!expanded) {

    return (
      <button
        type="button"
        disabled={context.busy}
        onClick={() => setExpanded(true)}
        className="inline-flex items-center gap-2 rounded-xl border border-red-500/40 px-4 py-2 text-sm font-semibold text-red-400 hover:bg-red-500/10 disabled:opacity-40"
      >

        <Flag className="h-4 w-4" />

        Reportar incumplimiento

      </button>
    );
  }


  return (
    <form
      onSubmit={submit}
      aria-label="Reportar incumplimiento"
      className="space-y-4 rounded-xl border border-red-500/30 bg-zinc-950 p-4"
    >

      <h4 className="flex items-center gap-2 font-bold text-white">

        <Flag className="h-4 w-4 text-red-400" />

        Reportar incumplimiento

      </h4>

      <p className="text-sm text-zinc-300 break-words">
        Suscripción: {subscriptionTitle}
      </p>

      <div className="space-y-2">

        <label
          htmlFor={`${formId}-reason`}
          className="block text-sm font-semibold text-zinc-300"
        >
          Motivo del reporte
        </label>

        <select
          id={`${formId}-reason`}
          required
          disabled={context.busy}
          value={reason}
          onChange={(event) => {

            const value = event.target.value;

            if (value === '') {
              setReason('');
              return;
            }

            const option = REASONS.find(
              (item) => item.value === value,
            );

            if (option) {
              setReason(option.value);
            }
          }}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white"
        >

          <option value="">
            Selecciona un motivo
          </option>

          {REASONS.map((item) => (
            <option
              key={item.value}
              value={item.value}
            >
              {item.label}
            </option>
          ))}

        </select>

      </div>

      <div className="space-y-2">

        <label
          htmlFor={`${formId}-description`}
          className="block text-sm font-semibold text-zinc-300"
        >
          Descripción del incumplimiento
        </label>

        <textarea
          id={`${formId}-description`}
          required
          minLength={20}
          maxLength={2000}
          rows={5}
          disabled={context.busy}
          value={description}
          onChange={(event) => {
            setDescription(event.target.value);
          }}
          placeholder="Describe los beneficios o condiciones que no fueron cumplidos..."
          className="w-full resize-y rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white placeholder:text-zinc-500"
        />

        <p className="text-right text-xs text-zinc-400">
          {description.length}/2000 caracteres
        </p>

      </div>

      <p className="text-xs text-zinc-400">
        Incluye información relevante del incumplimiento.
        No compartas contraseñas, datos bancarios ni
        información personal innecesaria.
      </p>

      <p className="text-xs text-zinc-400">
        Enviar un reporte no cancela tu suscripción
        ni genera una devolución automática.
      </p>

      <div className="flex flex-wrap justify-end gap-2">

        <button
          type="button"
          disabled={context.busy}
          onClick={reset}
          className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800 disabled:opacity-40"
        >
          Cancelar
        </button>

        <button
          type="submit"
          disabled={!valid || context.busy}
          className="rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40"
        >

          {context.busy
            ? 'Procesando...'
            : 'Enviar reporte'}

        </button>

      </div>

    </form>
  );
}


const REPORT_STATUS_INFO = {
  OPEN: {
    label: 'Pendiente',
    color: 'text-amber-400',
    border: 'border-amber-500/30',
  },
  IN_REVIEW: {
    label: 'En revisión',
    color: 'text-blue-400',
    border: 'border-blue-500/30',
  },
  RESOLVED: {
    label: 'Resuelto',
    color: 'text-emerald-400',
    border: 'border-emerald-500/30',
  },
  DISMISSED: {
    label: 'Desestimado',
    color: 'text-zinc-400',
    border: 'border-zinc-700',
  },
} as const;


type ReportFilter =
  | 'ALL'
  | DSubscriptionReport['status'];


function formatReportDate(value: string | null): string {

  if (!value) {
    return 'No disponible';
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return 'No disponible';
  }

  return date.toLocaleString('es-CL', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}


export function SubscriptionReportHistory() {

  const context = useSubscriptionReports();

  const filterId = useId();

  const [filter, setFilter] =
    useState<ReportFilter>('ALL');

  if (!context || context.reports === null) {
    return null;
  }

  const reports = context.reports;

  const statuses = [
    'OPEN',
    'IN_REVIEW',
    'RESOLVED',
    'DISMISSED',
  ] as const;

  const visibleReports = reports
    .filter(
      (report) =>
        filter === 'ALL' ||
        report.status === filter,
    )
    .sort(
      (a, b) =>
        Date.parse(b.created_at) -
        Date.parse(a.created_at) ||
        b.id - a.id,
    );

  return (

    <section
      aria-label="Mis reportes"
      className="rounded-2xl border border-zinc-800 bg-[#0e111a] p-5 space-y-5"
    >

      <div>

        <h3 className="text-lg font-bold text-white">
          Mis reportes
        </h3>

        <p className="mt-1 text-xs text-zinc-400">
          Consulta el estado de tus reportes y las
          resoluciones de la administración.
        </p>

      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">

        {statuses.map((status) => {

          const info = REPORT_STATUS_INFO[status];

          const count = reports.filter(
            (report) => report.status === status,
          ).length;

          return (

            <div
              key={status}
              className={`rounded-xl border bg-zinc-900/60 p-3 ${info.border}`}
            >

              <p className="text-xs text-zinc-400">
                {info.label}
              </p>

              <p className={`mt-1 text-2xl font-black ${info.color}`}>
                {count}
              </p>

            </div>
          );
        })}

      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">

        <p className="text-xs text-zinc-400">

          Total de reportes: {reports.length}

        </p>

        <div className="flex items-center gap-2">

          <label
            htmlFor={filterId}
            className="text-xs text-zinc-400"
          >
            Estado:
          </label>

          <select
            id={filterId}
            value={filter}
            onChange={(event) => {

              const value = event.target.value;

              if (value === 'ALL') {

                setFilter('ALL');

                return;
              }

              const selected = statuses.find(
                (status) => status === value,
              );

              if (selected) {
                setFilter(selected);
              }
            }}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-white"
          >

            <option value="ALL">
              Todos los estados
            </option>

            {statuses.map((status) => (

              <option
                key={status}
                value={status}
              >
                {REPORT_STATUS_INFO[status].label}
              </option>

            ))}

          </select>

        </div>

      </div>

      {visibleReports.length === 0 ? (

        <div className="rounded-xl border border-dashed border-zinc-700 p-6 text-center text-sm text-zinc-400">

          {reports.length === 0
            ? 'Todavía no has enviado reportes.'
            : 'No hay reportes con este estado.'}

        </div>

      ) : (

        <div className="space-y-3">

          {visibleReports.map((report) => {

            const info =
              REPORT_STATUS_INFO[report.status];

            const reason = REASONS.find(
              (item) => item.value === report.reason,
            );

            return (

              <article
                key={report.id}
                aria-label={`Reporte #${report.id}`}
                className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 space-y-4"
              >

                <div className="flex flex-wrap items-center justify-between gap-2">

                  <p className="text-sm font-bold text-white">

                    Reporte #{report.id}

                  </p>

                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${info.border} ${info.color}`}>

                    {info.label}

                  </span>

                </div>

                <div>

                  <h4 className="font-bold text-white break-words">

                    {report.subscription_title}

                  </h4>

                  <p className="mt-1 text-xs text-zinc-400 break-words">

                    Productor: {report.producer_name}

                  </p>

                </div>

                <div className="grid gap-3 text-xs text-zinc-400 sm:grid-cols-2">

                  <div>

                    <p className="font-semibold text-zinc-300">
                      Fecha del reporte
                    </p>

                    {formatReportDate(report.created_at)}

                  </div>

                  <div>

                    <p className="font-semibold text-zinc-300">
                      Inicio de la contratación
                    </p>

                    {formatReportDate(
                      report.contract_started_at,
                    )}

                  </div>

                </div>

                <div className="space-y-1">

                  <p className="text-xs text-zinc-400">
                    Motivo
                  </p>

                  <p className="text-sm font-semibold text-white">

                    {reason?.label ?? report.reason_label}

                  </p>

                </div>

                <div className="space-y-1">

                  <p className="text-xs text-zinc-400">
                    Descripción del incumplimiento
                  </p>

                  <p className="text-sm text-zinc-300 whitespace-pre-wrap break-words">

                    {report.description}

                  </p>

                </div>

                {report.status === 'OPEN' && (

                  <p className="rounded-lg bg-amber-500/10 p-3 text-xs text-amber-400">

                    Tu reporte está pendiente de revisión.

                  </p>

                )}

                {report.status === 'IN_REVIEW' && (

                  <p className="rounded-lg bg-blue-500/10 p-3 text-xs text-blue-400">

                    La administración está revisando tu caso.

                  </p>

                )}

                {(report.status === 'RESOLVED' ||
                  report.status === 'DISMISSED') && (

                  <div className={`rounded-xl border p-4 space-y-2 ${info.border}`}>

                    <p className={`text-sm font-bold ${info.color}`}>

                      Resolución administrativa

                    </p>

                    <p className="text-sm text-zinc-300 whitespace-pre-wrap break-words">

                      {report.resolution ||
                        'No hay una resolución disponible.'}

                    </p>

                    <p className="text-xs text-zinc-400">

                      Fecha de resolución: {' '}

                      {formatReportDate(
                        report.reviewed_at,
                      )}

                    </p>

                  </div>

                )}

                <p className="text-xs text-zinc-500">

                  Última actualización: {' '}

                  {formatReportDate(report.updated_at)}

                </p>

              </article>

            );
          })}

        </div>

      )}

    </section>
  );
}
