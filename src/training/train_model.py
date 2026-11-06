import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, GridSearchCV, cross_val_predict
from sklearn.metrics import mean_absolute_error, r2_score

def train_multimodal_model():
    dataset_path = Path("output/multimodal_training_dataset.csv")
    model_out_path = Path("output/multimodal_model.joblib")
    feature_names_path = Path("output/model_features.joblib")
    
    if not dataset_path.exists():
        print(f" Error: Could not find {dataset_path}")
        return
        
    df = pd.read_csv(dataset_path)
    
    target_cols = ['delivery_score', 'vocal_expression_score', 'body_language_score']
    exclude_cols = ['base_name'] + target_cols
    
    X = df.drop(columns=[col for col in exclude_cols if col in df.columns])
    y = df[target_cols]
    
    print(f"Training on {len(df)} presentations with {X.shape[1]} features...")
    
    rf = RandomForestRegressor(random_state=42)
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 5, 7],
        'min_samples_leaf': [2, 4]
    }
    
    kf = KFold(n_splits=min(5, max(2, len(df))), shuffle=True, random_state=42)
    
    print("Optimizing model...")
    grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=kf, scoring='neg_mean_absolute_error', n_jobs=-1)
    grid_search.fit(X, y)
    best_model = grid_search.best_estimator_
    
    # --- PERFORMANCE EVALUATION ---
    print("\n" + "="*50)
    print(" AI MODEL PERFORMANCE REPORT")
    print("="*50)
    
    # We use cross_val_predict to get an honest assessment of how the model performs on unseen data
    cv_predictions = cross_val_predict(best_model, X, y, cv=kf)
    
    # Calculate metrics for each specific category
    for i, category in enumerate(target_cols):
        y_true = y.iloc[:, i]
        y_pred = cv_predictions[:, i]
        
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        name_clean = category.replace('_', ' ').title()
        print(f"🔹 {name_clean}:")
        print(f"   • Error (MAE): ±{mae:.2f} points")
        print(f"   • Accuracy ($R^2$): {r2:.2f}")
    
    # Overall averages
    overall_mae = mean_absolute_error(y, cv_predictions)
    print(f"\n OVERALL AVERAGE ERROR: ±{overall_mae:.2f} points")
    print("="*50 + "\n")
    
    # Save the finalized model
    joblib.dump(best_model, model_out_path)
    joblib.dump(X.columns.tolist(), feature_names_path)
    print(f" Model saved successfully!")

if __name__ == "__main__":
    train_multimodal_model()