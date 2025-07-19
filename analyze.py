import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter
import re
import psycopg2
from sqlalchemy import create_engine, text
import os


class TransactionAnalyzer:
    def __init__(self, db_config=None, table_name=None, data_file=None):
        """Initialize the analyzer with transaction data"""
        self.df = None
        self.failure_events = []
        self.success_events = []

        if db_config and table_name:
            self.load_data_from_database(db_config, table_name)
    

    def load_data_from_database(self, db_config, table_name="transaction_events"):
        """Load data from PostgreSQL database"""
        try:
            # Create connection string
            if isinstance(db_config, dict):
                connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            else:
                connection_string = db_config  # Assume it's already a connection string

            # Create engine
            engine = create_engine(connection_string)

            # SQL query to fetch transaction events
            query = f"""
            SELECT 
                account_id,
                affected_service,
                alert_description,
                aml_risk_score,
                auto_retry_enabled,
                balance_after,
                balance_before,
                block_hash,
                block_number,
                bridge_fee_bps,
                bridge_protocol,
                confirmations,
                credit_amount,
                crypto_amount,
                crypto_token,
                debit_amount,
                defi_protocol,
                dest_chain_id,
                document_types,
                error_code,
                error_message,
                estimated_impact,
                event_index,
                event_type,
                exchange_rate,
                fiat_amount,
                fiat_currency,
                flow_type,
                from_address,
                from_network,
                gas_cost_native,
                gas_price_gwei,
                gas_used,
                incident_id,
                kyc_provider,
                kyc_session_id,
                kyc_status,
                ledger_entry_id,
                ledger_entry_type,
                ledger_reference,
                lp_fee_bps,
                merkle_root,
                min_received,
                mitigation_steps,
                network,
                next_retry_in,
                oncall_team,
                pep_check,
                pool_address,
                proof_hash,
                protocol_network,
                protocol_tvl,
                protocol_type,
                provider,
                relay_node,
                retry_count,
                risk_score,
                sanctions_check,
                severity,
                sla_breach,
                slippage_tolerance,
                source_chain_id,
                timestamp,
                to_address,
                to_network,
                transaction_id,
                tx_hash,
                tx_status,
                user_id,
                user_tier,
                verification_level
            FROM {table_name}
            ORDER BY transaction_id, event_index, timestamp
            """

            # Load data
            print(f"Connecting to database and loading data from {table_name}...")
            self.df = pd.DataFrame(engine.connect().execute(text(query)))

            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], errors='coerce')

        except Exception as e:
            print(f"Error loading data from database: {e}")
            return

    def categorize_events(self):
        """Categorize events into failure and success types"""
        failure_keywords = [
            "failed",
            "failure",
            "error",
            "timeout",
            "rejected",
            "cancelled",
            "reverted",
            "underpriced",
            "insufficient",
            "invalid",
            "denied",
        ]

        success_keywords = [
            "completed",
            "success",
            "confirmed",
            "approved",
            "processed",
            "validated",
        ]

        self.failure_events = []
        self.success_events = []

        for idx, row in self.df.iterrows():
            event_type = str(row["event_type"]).lower()
            error_message = str(row["error_message"]).lower()

            # Check if it's a failure event
            is_failure = any(keyword in event_type for keyword in failure_keywords)
            is_failure = is_failure or any(
                keyword in error_message for keyword in failure_keywords
            )
            is_failure = is_failure or "payment_failure" in error_message

            # Check if it's a success event
            is_success = any(keyword in event_type for keyword in success_keywords)

            if is_failure:
                self.failure_events.append(idx)
            elif is_success:
                self.success_events.append(idx)

        print(
            f"Identified {len(self.failure_events)} failure events and {len(self.success_events)} success events"
        )

    def analyze_failure_patterns(self):
        """Analyze patterns in failure events"""
        if not self.failure_events:
            print("No failure events found to analyze")
            return

        failure_df = self.df.loc[self.failure_events]

        print("\n" + "=" * 60)
        print("FAILURE ANALYSIS REPORT")
        print("=" * 60)

        # Event type distribution
        print("\n📊 Failure Event Types:")
        event_counts = failure_df["event_type"].value_counts()
        for event, count in event_counts.head(10).items():
            print(f"  • {event}: {count} occurrences")

        # Failure reasons
        print("\n🔍 Failure Reasons:")
        error_messages = failure_df["error_message"].value_counts()
        for reason, count in error_messages.head(10).items():
            if reason and reason != "nan":
                print(f"  • {reason}: {count} occurrences")

        # Error codes and messages
        error_codes = failure_df["error_code"].dropna().value_counts()
        if not error_codes.empty:
            print("\n⚠️  Error Codes:")
            for code, count in error_codes.head(5).items():
                print(f"  • {code}: {count} occurrences")

        # Affected services
        services = failure_df["affected_service"].dropna().value_counts()
        if not services.empty:
            print("\n🔧 Affected Services:")
            for service, count in services.head(5).items():
                print(f"  • {service}: {count} failures")

        # Time-based analysis
        if not failure_df["timestamp"].isna().all():
            print("\n📅 Temporal Distribution:")
            failure_df["hour"] = failure_df["timestamp"].dt.hour
            hourly_failures = failure_df["hour"].value_counts().sort_index()
            peak_hour = hourly_failures.idxmax()
            print(
                f"  • Peak failure time: {peak_hour}:00 hour ({hourly_failures[peak_hour]} failures)"
            )
            print(
                f"  • Total time span: {failure_df['timestamp'].min()} to {failure_df['timestamp'].max()}"
            )

        return failure_df

    def diagnose_specific_failures(self, failure_df):
        """Provide specific diagnosis for different types of failures"""
        print("\n" + "=" * 60)
        print("DETAILED FAILURE DIAGNOSIS")
        print("=" * 60)

        # Network/Blockchain related failures
        blockchain_failures = failure_df[
            failure_df["error_message"].str.contains(
                "payment_failure_technical", na=False
            )
            | failure_df["error_code"].str.contains(
                "REPLACEMENT_UNDERPRICED|EXECUTION_REVERTED", na=False
            )
        ]

        if not blockchain_failures.empty:
            print("\n🌐 BLOCKCHAIN/NETWORK ISSUES:")
            print(f"  Found {len(blockchain_failures)} blockchain-related failures")

            for idx, row in blockchain_failures.iterrows():
                print(f"\n  Transaction ID: {row['transaction_id']}")
                print(f"  • Event: {row['event_type']}")
                print(f"  • Network: {row['to_network']}/{row['network']}")
                print(f"  • Error: {row['error_code']} - {row['error_message']}")
                print(f"  • Recommended Action: {row['mitigation_steps']}")

                if row["error_code"] == "REPLACEMENT_UNDERPRICED":
                    print(
                        "  🔧 DIAGNOSIS: Gas price too low - transaction stuck in mempool"
                    )
                    print("     SOLUTION: Increase gas price and resubmit transaction")

                elif row["error_code"] == "EXECUTION_REVERTED":
                    print("  🔧 DIAGNOSIS: Smart contract execution failed")
                    print(
                        "     SOLUTION: Check contract state, parameters, and gas limits"
                    )

        # Service degradation issues
        service_issues = failure_df[failure_df["service_status"].notna()]
        if not service_issues.empty:
            print("\n🔧 SERVICE DEGRADATION ISSUES:")
            service_status_counts = service_issues["service_status"].value_counts()
            for status, count in service_status_counts.items():
                print(f"  • {status}: {count} incidents")

        # User impact analysis
        user_impact = failure_df["users_affected"].dropna()
        if not user_impact.empty:
            total_affected = user_impact.str.extract("(\d+)").astype(int).sum().iloc[0]
            print(f"\n👥 USER IMPACT:")
            print(f"  • Total users affected: {total_affected}")
            print(f"  • Average per incident: {total_affected / len(user_impact):.1f}")

    def analyze_failure_progression(self):
        """Analyze how failures progress through different steps"""
        print("\n" + "=" * 60)
        print("FAILURE PROGRESSION ANALYSIS")
        print("=" * 60)

        # Group by transaction ID to see progression
        transaction_groups = self.df.groupby("transaction_id")

        failed_transactions = []

        for tx_id, group in transaction_groups:
            if group["error_message"].str.contains("payment_failure", na=False).any():
                failed_transactions.append(
                    {
                        "transaction_id": tx_id,
                        "steps": group["step"].tolist(),
                        "events": group["event_type"].tolist(),
                        "timeline": group["timestamp"].tolist(),
                    }
                )

        if failed_transactions:
            print(
                f"\n📈 Analyzed {len(failed_transactions)} failed transaction progressions"
            )

            # Show a sample progression
            sample_tx = failed_transactions[0]
            print(
                f"\n🔍 Sample Transaction Progression ({sample_tx['transaction_id']}):"
            )

            for i, (step, event) in enumerate(
                zip(sample_tx["steps"], sample_tx["events"])
            ):
                if pd.notna(step):
                    print(f"  Step {int(step)}: {event}")

            # Common failure points
            all_failure_steps = []
            for tx in failed_transactions:
                failure_step = max([s for s in tx["steps"] if pd.notna(s)], default=0)
                all_failure_steps.append(failure_step)

            if all_failure_steps:
                step_counter = Counter(all_failure_steps)
                print(f"\n📊 Most Common Failure Points:")
                for step, count in step_counter.most_common(5):
                    print(f"  • Step {int(step)}: {count} transactions failed")

    def generate_recommendations(self):
        """Generate actionable recommendations based on analysis"""
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)

    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        if self.df is None:
            print("No data loaded. Please check the data file.")
            return

        print("Starting transaction failure analysis...")

        # Step 1: Categorize events
        self.categorize_events()

        # Step 2: Analyze failure patterns
        failure_df = self.analyze_failure_patterns()

        # Step 3: Detailed diagnosis
        if failure_df is not None and not failure_df.empty:
            self.diagnose_specific_failures(failure_df)

        # Step 4: Analyze failure progression
        self.analyze_failure_progression()

        # Step 5: Generate recommendations
        self.generate_recommendations()

    def get_database_statistics(self, db_config, table_name):
        """Get basic statistics from the database"""
        try:
            if isinstance(db_config, dict):
                connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            else:
                connection_string = db_config

            engine = create_engine(connection_string)

            stats_query = f"""
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT transaction_id) as unique_transactions,
                COUNT(DISTINCT user_id) as unique_users,
                MIN(timestamp) as earliest_event,
                MAX(timestamp) as latest_event,
                COUNT(*) FILTER (WHERE error_message LIKE '%failure%') as failure_events,
                COUNT(DISTINCT event_type) as unique_event_types
            FROM {table_name}
            """

            stats_df = pd.DataFrame(engine.connect().execute(text(stats_query)))

            print("\n" + "=" * 50)
            print("DATABASE STATISTICS")
            print("=" * 50)
            for col in stats_df.columns:
                print(f"{col}: {stats_df[col].iloc[0]}")

            # Get top event types
            event_types_query = f"""
            SELECT 
                event_type, COUNT(*) as count 
            FROM {table_name} 
            WHERE event_type IS NOT NULL 
            GROUP BY event_type 
            ORDER BY count DESC 
            LIMIT 10
            """

            event_types_df = pd.DataFrame(engine.connect().execute(text(event_types_query)))
            
            print(f"\nTop Event Types:")
            for _, row in event_types_df.iterrows():
                print(f"  • {row['event_type']}: {row['count']}")

        except Exception as e:
            print(f"Error getting database statistics: {e})")

        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)


# Database connection examples and utility functions
def create_db_config_from_env():
    """Create database configuration from environment variables"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", 5431),
        "database": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


def create_db_config(host, port, database, user, password):
    """Create database configuration dictionary"""
    return {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }


# Usage examples
if __name__ == "__main__":

    # Example 1: Read from PostgreSQL database
    print("=== DATABASE ANALYSIS EXAMPLE ===")

    db_config = create_db_config_from_env()

    try:
        # Initialize analyzer with database connection
        analyzer = TransactionAnalyzer(
            db_config=db_config, table_name="onchain_fiat_transaction_data"
        )

        # Get database statistics first
        analyzer.get_database_statistics(db_config, "onchain_fiat_transaction_data")

        # Run complete analysis
        analyzer.run_full_analysis()

    except Exception as e:
        print(f"Database connection failed: {e}")
        print("\nFalling back to uploaded file analysis...")

        # Fallback: analyze uploaded file data
        analyzer = TransactionAnalyzer()
        analyzer.run_full_analysis()

    print("\n" + "=" * 60)
    print("ADDITIONAL DATABASE UTILITIES")
    print("=" * 60)
    print("To set up the database:")
    print("1. analyzer.create_database_tables(db_config)")
    print("2. analyzer.import_data_to_database(db_config)")
    print("3. analyzer.get_database_statistics(db_config)")
