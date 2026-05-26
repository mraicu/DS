import { FormEvent, useEffect, useState } from "react";

import {
  CategoricalEncoding,
  ColumnProfile,
  DatasetConfigResponse,
  MLAlgorithmType,
  MLStateResponse,
  dropMissingRows,
  getDatasetConfig,
  getDatasetDescribe,
  getDatasetDtypes,
  getDatasetHead,
  getDatasetShape,
  getDatasetTail,
  getMLState,
  predictWithModel,
  trainModel,
  uploadDataset,
} from "../api";

type DashboardPageProps = {
  session: { token: string; username: string; email: string };
  onLogout: () => void;
};

function buildInputDefaults(featureProfiles: ColumnProfile[]): Record<string, string> {
  const values: Record<string, string> = {};
  featureProfiles.forEach((profile) => {
    values[profile.name] = profile.is_categorical ? profile.sample_values[0] ?? "" : "";
  });
  return values;
}

export function DashboardPage({ session, onLogout }: DashboardPageProps) {
  const [shape, setShape] = useState<{ rows: number; columns: number } | null>(null);
  const [datasetConfig, setDatasetConfig] = useState<DatasetConfigResponse | null>(null);
  const [mlState, setMlState] = useState<MLStateResponse | null>(null);
  const [tableRows, setTableRows] = useState<Record<string, unknown>[]>([]);
  const [tableTitle, setTableTitle] = useState("Dataset preview");
  const [nHead, setNHead] = useState(5);
  const [nTail, setNTail] = useState(5);
  const [datasetError, setDatasetError] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isCleaningDataset, setIsCleaningDataset] = useState(false);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<MLAlgorithmType>("regression");
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [targetColumn, setTargetColumn] = useState("");
  const [categoricalEncoding, setCategoricalEncoding] = useState<CategoricalEncoding>("one_hot");
  const [trainError, setTrainError] = useState("");
  const [trainMessage, setTrainMessage] = useState("");
  const [isTraining, setIsTraining] = useState(false);
  const [dynamicInputs, setDynamicInputs] = useState<Record<string, string>>({});
  const [dynamicPrediction, setDynamicPrediction] = useState<string | number | null>(null);
  const [dynamicPredictionError, setDynamicPredictionError] = useState("");
  const [isPredictingDynamic, setIsPredictingDynamic] = useState(false);

  async function refreshDatasetState() {
    const [shapeResponse, configResponse, mlStateResponse] = await Promise.all([
      getDatasetShape(session.token),
      getDatasetConfig(session.token),
      getMLState(session.token),
    ]);
    setShape(shapeResponse);
    setDatasetConfig(configResponse);
    setMlState(mlStateResponse);
    if (!mlStateResponse.trained_model) {
      setDynamicPrediction(null);
      setDynamicPredictionError("");
    }
  }

  useEffect(() => {
    refreshDatasetState().catch(() => {
      onLogout();
    });
  }, [session.token, onLogout]);

  useEffect(() => {
    if (!mlState) {
      return;
    }

    const availableColumns = new Set(mlState.columns.map((column) => column.name));
    setSelectedFeatures((previous) => previous.filter((column) => availableColumns.has(column)));
    setTargetColumn((previous) => (previous && availableColumns.has(previous) ? previous : ""));
  }, [mlState]);

  useEffect(() => {
    if (targetColumn && selectedFeatures.includes(targetColumn)) {
      setTargetColumn("");
    }
  }, [selectedFeatures, targetColumn]);

  useEffect(() => {
    if (mlState?.trained_model) {
      setDynamicInputs(buildInputDefaults(mlState.trained_model.feature_profiles));
    }
  }, [mlState?.trained_model]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDatasetError("");
    setUploadMessage("");
    setTrainMessage("");

    const formData = new FormData(event.currentTarget);
    const file = formData.get("dataset");
    if (!(file instanceof File) || file.size === 0) {
      setDatasetError("Choose a CSV file before uploading");
      return;
    }

    setIsUploading(true);
    try {
      const uploadResponse = await uploadDataset(session.token, file);
      setDatasetConfig(uploadResponse);
      await refreshDatasetState();
      setTableRows([]);
      setTableTitle("Dataset preview");
      setUploadMessage(`Loaded ${uploadResponse.dataset_name} as the active dataset`);
      event.currentTarget.reset();
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to upload dataset");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDropMissingRows() {
    setDatasetError("");
    setUploadMessage("");
    setTrainMessage("");
    setIsCleaningDataset(true);
    try {
      const result = await dropMissingRows(session.token);
      setDatasetConfig(result);
      await refreshDatasetState();
      setTableRows([]);
      setTableTitle("Dataset preview");
      setUploadMessage(`Removed ${result.removed_rows} rows with empty values from ${result.dataset_name}`);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to remove empty rows");
    } finally {
      setIsCleaningDataset(false);
    }
  }

  async function showDtypes() {
    setDatasetError("");
    try {
      const result = await getDatasetDtypes(session.token);
      setTableTitle("Column names and data types");
      setTableRows(result.rows);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to load column types");
    }
  }

  async function showHead() {
    setDatasetError("");
    try {
      const result = await getDatasetHead(session.token, nHead);
      setTableTitle(`First ${nHead} rows`);
      setTableRows(result.rows);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to load first rows");
    }
  }

  async function showTail() {
    setDatasetError("");
    try {
      const result = await getDatasetTail(session.token, nTail);
      setTableTitle(`Last ${nTail} rows`);
      setTableRows(result.rows);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to load last rows");
    }
  }

  async function showDescribe() {
    setDatasetError("");
    try {
      const result = await getDatasetDescribe(session.token);
      setTableTitle("Basic dataset statistics");
      setTableRows(result.rows);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to load statistics");
    }
  }

  function toggleFeature(column: string) {
    setSelectedFeatures((previous) =>
      previous.includes(column) ? previous.filter((value) => value !== column) : [...previous, column],
    );
  }

  async function handleTrainModel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setTrainError("");
    setTrainMessage("");
    setDynamicPrediction(null);
    setDynamicPredictionError("");

    if (selectedFeatures.length === 0) {
      setTrainError("Choose at least one feature column");
      return;
    }

    if (selectedAlgorithm !== "clustering" && !targetColumn) {
      setTrainError("Choose a target column for regression or classification");
      return;
    }

    setIsTraining(true);
    try {
      const result = await trainModel(session.token, {
        algorithm_type: selectedAlgorithm,
        feature_columns: selectedFeatures,
        target_column: selectedAlgorithm === "clustering" ? null : targetColumn,
        categorical_encoding: categoricalEncoding,
      });
      setMlState((previous) =>
        previous
          ? {
              ...previous,
              trained_model: result.trained_model,
            }
          : previous,
      );
      setDynamicInputs(buildInputDefaults(result.trained_model.feature_profiles));
      setTrainMessage(result.message);
    } catch (err) {
      setTrainError(err instanceof Error ? err.message : "Model training failed");
    } finally {
      setIsTraining(false);
    }
  }

  async function handleDynamicPrediction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDynamicPrediction(null);
    setDynamicPredictionError("");
    setIsPredictingDynamic(true);
    try {
      const result = await predictWithModel(session.token, { values: dynamicInputs });
      setDynamicPrediction(result.prediction);
    } catch (err) {
      setDynamicPredictionError(err instanceof Error ? err.message : "Prediction failed");
    } finally {
      setIsPredictingDynamic(false);
    }
  }

  const tableColumns = tableRows.length > 0 ? Object.keys(tableRows[0]) : [];
  const datasetColumns = mlState?.columns ?? [];
  const selectedFeatureProfiles = datasetColumns.filter((column) => selectedFeatures.includes(column.name));
  const hasCategoricalSelection = selectedFeatureProfiles.some((column) => column.is_categorical);
  const trainedModel = mlState?.trained_model ?? null;

  return (
    <main className="page dashboard-page">
      <header className="topbar">
        <div>
          <h1>Dashboard</h1>
          <p>
            Logged in as <strong>{session.username}</strong>
          </p>
        </div>
        <button onClick={onLogout}>Log out</button>
      </header>

      <section className="card dataset-card">
        <h2>Dataset Tools</h2>
        <p>
          Active dataset: <strong>{datasetConfig?.dataset_name ?? "..."}</strong>{" "}
          {datasetConfig && (datasetConfig.is_default_dataset ? "(default)" : "(uploaded)")}
        </p>
        <p>
          Rows: <strong>{shape?.rows ?? "..."}</strong> | Columns: <strong>{shape?.columns ?? "..."}</strong>
        </p>

        <form onSubmit={handleUpload} className="upload-row">
          <input type="file" name="dataset" accept=".csv,text/csv" />
          <button type="submit" disabled={isUploading}>
            {isUploading ? "Uploading..." : "Upload CSV"}
          </button>
        </form>
        {uploadMessage && <p className="success">{uploadMessage}</p>}

        <div className="dataset-actions">
          <button type="button" onClick={handleDropMissingRows} disabled={isCleaningDataset}>
            {isCleaningDataset ? "Removing empty rows..." : "Remove empty rows"}
          </button>

          <button type="button" onClick={showDtypes}>
            Show columns and types
          </button>

          <div className="inline-action">
            <input type="number" min={1} value={nHead} onChange={(event) => setNHead(Number(event.target.value) || 1)} />
            <button type="button" onClick={showHead}>
              Show first N rows
            </button>
          </div>

          <div className="inline-action">
            <input type="number" min={1} value={nTail} onChange={(event) => setNTail(Number(event.target.value) || 1)} />
            <button type="button" onClick={showTail}>
              Show last N rows
            </button>
          </div>

          <button type="button" onClick={showDescribe}>
            Show basic statistics
          </button>
        </div>

        <h3>{tableTitle}</h3>
        {tableRows.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {tableColumns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableRows.map((row, index) => (
                  <tr key={index}>
                    {tableColumns.map((column) => (
                      <td key={`${index}-${column}`}>{String(row[column] ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {datasetError && <p className="error">{datasetError}</p>}
      </section>

      <section className="card ml-card">
        <h2>AI Model Studio</h2>
        <p>Select features, choose an algorithm, train a model on the active dataset, and use it for predictions.</p>

        <form onSubmit={handleTrainModel} className="form-grid">
          <label>
            Algorithm type
            <select value={selectedAlgorithm} onChange={(event) => setSelectedAlgorithm(event.target.value as MLAlgorithmType)}>
              <option value="regression">Regression</option>
              <option value="classification">Classification</option>
              <option value="clustering">Clustering</option>
            </select>
          </label>

          <label>
            Categorical preprocessing
            <select
              value={categoricalEncoding}
              onChange={(event) => setCategoricalEncoding(event.target.value as CategoricalEncoding)}
              disabled={!hasCategoricalSelection}
            >
              <option value="one_hot">get_dummies</option>
              <option value="ordinal">OrdinalEncoder.fit_transform</option>
            </select>
          </label>

          {selectedAlgorithm !== "clustering" && (
            <label>
              Target column
              <select value={targetColumn} onChange={(event) => setTargetColumn(event.target.value)}>
                <option value="">Select a target column</option>
                {datasetColumns
                  .filter((column) => !selectedFeatures.includes(column.name))
                  .map((column) => (
                    <option key={column.name} value={column.name}>
                      {column.name}
                    </option>
                  ))}
              </select>
            </label>
          )}

          <div>
            <h3>Feature columns</h3>
            <div className="feature-grid">
              {datasetColumns.map((column) => (
                <label key={column.name} className="feature-option">
                  <input
                    type="checkbox"
                    checked={selectedFeatures.includes(column.name)}
                    onChange={() => toggleFeature(column.name)}
                  />
                  <span>{column.name}</span>
                  <small>
                    {column.dtype} | missing: {column.missing_count} | unique: {column.unique_count}
                  </small>
                </label>
              ))}
            </div>
          </div>

          {trainError && <p className="error">{trainError}</p>}
          {trainMessage && <p className="success">{trainMessage}</p>}

          <button type="submit" disabled={isTraining}>
            {isTraining ? "Training model..." : "Train model"}
          </button>
        </form>

        {trainedModel && (
          <>
            <div className="trained-model-summary">
              <h3>Trained model</h3>
              <p>
                Type: <strong>{trainedModel.algorithm_type}</strong> | Features:{" "}
                <strong>{trainedModel.feature_columns.join(", ")}</strong>
              </p>
              <p>
                Target: <strong>{trainedModel.target_column ?? "No target"}</strong> | Encoding:{" "}
                <strong>{trainedModel.categorical_encoding}</strong>
              </p>
              <p>
                Rows used for training: <strong>{trainedModel.training_rows}</strong>
              </p>
            </div>

            <form onSubmit={handleDynamicPrediction} className="form-grid two-columns">
              {trainedModel.feature_profiles.map((profile) => (
                <label key={profile.name}>
                  {profile.name}
                  {profile.is_categorical ? (
                    <select
                      value={dynamicInputs[profile.name] ?? ""}
                      onChange={(event) =>
                        setDynamicInputs((previous) => ({
                          ...previous,
                          [profile.name]: event.target.value,
                        }))
                      }
                    >
                      <option value="">Select a value</option>
                      {profile.sample_values.map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="number"
                      step="any"
                      value={dynamicInputs[profile.name] ?? ""}
                      onChange={(event) =>
                        setDynamicInputs((previous) => ({
                          ...previous,
                          [profile.name]: event.target.value,
                        }))
                      }
                    />
                  )}
                </label>
              ))}

              <button type="submit" disabled={isPredictingDynamic}>
                {isPredictingDynamic ? "Predicting..." : "Predict"}
              </button>
            </form>

            {dynamicPrediction !== null && (
              <p className="prediction-result">
                Result: {String(dynamicPrediction)}
                {trainedModel.algorithm_type === "clustering" ? " cluster" : ""}
              </p>
            )}
            {dynamicPredictionError && <p className="error">{dynamicPredictionError}</p>}
          </>
        )}
      </section>
    </main>
  );
}
