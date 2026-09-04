import re
with open("app/domain/gateway.py", "r") as f:
    content = f.read()

# Remove the short circuiting
old_block = """            if sem_result.status in ("FAIL", "REVIEW"):
                raise SemanticDrift(f"Semantic drift detected: {sem_result.status}")
                
            state.transition_to(TransactionState.SEMANTIC_ANALYZED)
            await self._log(tx_id, TransactionState.SEMANTIC_ANALYZED, **context)
            
        except Exception as e:
            await self.idempotency.release(reservation_key, tx_id)
            if not isinstance(e, SemanticDrift):
                raise
            state.transition_to(TransactionState.SEMANTIC_DRIFT)
            context["failure_reason"] = str(e)
            await self._log(tx_id, TransactionState.SEMANTIC_DRIFT, **context)
            raise"""

new_block = """            state.transition_to(TransactionState.SEMANTIC_ANALYZED)
            await self._log(tx_id, TransactionState.SEMANTIC_ANALYZED, **context)
            
        except Exception as e:
            await self.idempotency.release(reservation_key, tx_id)
            raise"""
content = content.replace(old_block, new_block)

# Add passing the semantic result to OPA
content = content.replace("""            opa_input = {
                "mandate": open_mandate.constraints.model_dump(mode='json'),
                "cart": request.cart.model_dump(mode='json'),
                "current_time": int(time.time())
            }""", """            opa_input = {
                "mandate": open_mandate.constraints.model_dump(mode='json'),
                "cart": request.cart.model_dump(mode='json'),
                "semantic": sem_result.model_dump(mode='json'),
                "current_time": int(time.time())
            }""")

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
